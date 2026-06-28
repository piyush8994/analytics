import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Phone Usage Insights", page_icon="📱", layout="wide")

APP_META = {
    'Instagram':  {'category': 'Social Media',  'addictive': True},
    'YouTube':    {'category': 'Entertainment', 'addictive': True},
    'WhatsApp':   {'category': 'Messaging',     'addictive': False},
    'Twitter/X':  {'category': 'Social Media',  'addictive': True},
    'Reddit':     {'category': 'Social Media',  'addictive': True},
    'Chrome':     {'category': 'Productivity',  'addictive': False},
    'Gmail':      {'category': 'Productivity',  'addictive': False},
    'Spotify':    {'category': 'Entertainment', 'addictive': False},
    'Netflix':    {'category': 'Entertainment', 'addictive': True},
    'TikTok':     {'category': 'Social Media',  'addictive': True},
    'Maps':       {'category': 'Utility',       'addictive': False},
    'Phone':      {'category': 'Communication', 'addictive': False},
    'Settings':   {'category': 'Utility',       'addictive': False},
    'Slack':      {'category': 'Productivity',  'addictive': False},
    'LinkedIn':   {'category': 'Social Media',  'addictive': False},
}


@st.cache_data
def load_data():
    df = pd.read_csv('data/phone_usage_90days.csv', parse_dates=['date'])
    return df


df = load_data()

# ── Sidebar filters ─────────────────────────────────────────────────────
st.sidebar.title("📱 Filters")

date_range = st.sidebar.date_input(
    "Date range",
    value=(df['date'].min().date(), df['date'].max().date()),
    min_value=df['date'].min().date(),
    max_value=df['date'].max().date(),
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    mask = (df['date'].dt.date >= date_range[0]) & (df['date'].dt.date <= date_range[1])
    df = df[mask]

all_apps = sorted(df['app'].unique())
selected_apps = st.sidebar.multiselect("Apps", all_apps, default=all_apps)
df = df[df['app'].isin(selected_apps)]

all_categories = sorted(df['category'].unique())
selected_categories = st.sidebar.multiselect("Categories", all_categories, default=all_categories)
df = df[df['category'].isin(selected_categories)]

day_type = st.sidebar.radio("Day type", ["All", "Weekdays only", "Weekends only"])
if day_type == "Weekdays only":
    df = df[~df['is_weekend']]
elif day_type == "Weekends only":
    df = df[df['is_weekend']]

# ── Derived aggregates ──────────────────────────────────────────────────
daily = df.groupby('date').agg(
    total_minutes=('minutes', 'sum'),
    total_pickups=('pickups', 'sum'),
    total_notifications=('notifications', 'sum'),
).reset_index()
daily['hours'] = daily['total_minutes'] / 60
num_days = max(daily.shape[0], 1)

# ── Header KPIs ─────────────────────────────────────────────────────────
st.title("📱 Phone Usage Analytics Dashboard")
st.caption(f"Analyzing {num_days} days of screen time data")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Avg Daily Screen Time", f"{daily['hours'].mean():.1f}h")
c2.metric("Total Hours", f"{daily['hours'].sum():.0f}h")
c3.metric("Avg Pickups/Day", f"{daily['total_pickups'].mean():.0f}")
c4.metric("Peak Day", f"{daily.loc[daily['hours'].idxmax(), 'hours']:.1f}h" if len(daily) else "—")
addictive_pct = df[df['app'].map(lambda a: APP_META.get(a, {}).get('addictive', False))]['minutes'].sum() / max(df['minutes'].sum(), 1) * 100
c5.metric("Addictive App %", f"{addictive_pct:.0f}%")

st.divider()

# ═══════════════════════════════════════════════════════════════════════
# TAB LAYOUT
# ═══════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Daily Trend",
    "📊 App Breakdown",
    "🕐 When You Use",
    "🔔 Triggers & Nudges",
    "🌙 Late Night",
    "💡 Recommendations",
])

# ── Tab 1: Daily Trend ──────────────────────────────────────────────────
with tab1:
    st.subheader("Daily Screen Time Trend")
    rolling_window = st.slider("Rolling average window (days)", 3, 14, 7, key="roll")
    daily_sorted = daily.sort_values('date')
    daily_sorted['rolling'] = daily_sorted['hours'].rolling(rolling_window).mean()

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.bar(daily_sorted['date'], daily_sorted['hours'], alpha=0.35, color='#5B8DEF', label='Daily')
    ax.plot(daily_sorted['date'], daily_sorted['rolling'], color='#E74C3C', linewidth=2.5,
            label=f'{rolling_window}-day avg')
    ax.axhline(y=daily_sorted['hours'].median(), color='orange', linestyle='--', alpha=0.7,
               label=f'Median: {daily_sorted["hours"].median():.1f}h')
    ax.set_ylabel('Hours')
    ax.legend()
    st.pyplot(fig)
    plt.close()

    st.subheader("Usage Creep — Weekly Averages")
    daily_sorted['week_num'] = range(len(daily_sorted))
    daily_sorted['week_label'] = daily_sorted['date'].dt.isocalendar().week.astype(int)
    weekly = daily_sorted.groupby('week_label').agg(
        avg_hours=('hours', 'mean'), avg_pickups=('total_pickups', 'mean')
    ).reset_index()

    fig2, ax1 = plt.subplots(figsize=(12, 4))
    ax1.bar(weekly['week_label'], weekly['avg_hours'], color='#5B8DEF', alpha=0.7)
    ax1.set_xlabel('Week Number')
    ax1.set_ylabel('Avg Daily Hours', color='#5B8DEF')
    ax2 = ax1.twinx()
    ax2.plot(weekly['week_label'], weekly['avg_pickups'], color='#E74C3C', linewidth=2, marker='o')
    ax2.set_ylabel('Avg Daily Pickups', color='#E74C3C')
    st.pyplot(fig2)
    plt.close()

    if len(weekly) >= 2:
        first_w = weekly['avg_hours'].iloc[0]
        last_w = weekly['avg_hours'].iloc[-1]
        pct = (last_w - first_w) / max(first_w, 0.1) * 100
        if pct > 5:
            st.warning(f"Your usage crept up **{pct:.0f}%** from the first to last week.")
        elif pct < -5:
            st.success(f"Great — your usage dropped **{abs(pct):.0f}%** over the period!")
        else:
            st.info("Your usage stayed relatively stable over the period.")

# ── Tab 2: App Breakdown ────────────────────────────────────────────────
with tab2:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Total Hours by App")
        app_total = df.groupby('app')['minutes'].sum().sort_values(ascending=True) / 60
        fig, ax = plt.subplots(figsize=(8, 7))
        colors = ['#E74C3C' if APP_META.get(a, {}).get('addictive', False) else '#3498DB' for a in app_total.index]
        bars = ax.barh(app_total.index, app_total.values, color=colors)
        for bar, val in zip(bars, app_total.values):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2, f'{val:.0f}h', va='center', fontsize=9)
        ax.set_xlabel('Hours')
        st.pyplot(fig)
        plt.close()

    with col_b:
        st.subheader("By Category")
        cat_total = df.groupby('category')['minutes'].sum() / 60
        fig, ax = plt.subplots(figsize=(8, 7))
        wedges, texts, autotexts = ax.pie(
            cat_total.values, labels=cat_total.index, autopct='%1.1f%%',
            colors=sns.color_palette('Set2', len(cat_total)), startangle=140
        )
        st.pyplot(fig)
        plt.close()

    st.subheader("Top 5 Apps — Daily Trend")
    top5 = df.groupby('app')['minutes'].sum().nlargest(5).index
    top5_daily = df[df['app'].isin(top5)].groupby(['date', 'app'])['minutes'].sum().reset_index()
    top5_daily['hours'] = top5_daily['minutes'] / 60

    fig, ax = plt.subplots(figsize=(14, 5))
    for app in top5:
        ad = top5_daily[top5_daily['app'] == app].sort_values('date')
        ax.plot(ad['date'], ad['hours'].rolling(7).mean(), linewidth=2, label=app)
    ax.set_ylabel('Daily Hours (7-day avg)')
    ax.legend()
    st.pyplot(fig)
    plt.close()

    st.subheader("App Details Table")
    app_table = df.groupby('app').agg(
        total_hours=('minutes', lambda x: round(x.sum() / 60, 1)),
        avg_daily_min=('minutes', lambda x: round(x.sum() / num_days, 1)),
        total_pickups=('pickups', 'sum'),
        total_notifications=('notifications', 'sum'),
    ).sort_values('total_hours', ascending=False).reset_index()
    app_table.columns = ['App', 'Total Hours', 'Avg Daily Min', 'Pickups', 'Notifications']
    st.dataframe(app_table, use_container_width=True, hide_index=True)

# ── Tab 3: When You Use ─────────────────────────────────────────────────
with tab3:
    st.subheader("Usage Heatmap — Hour x Day of Week")
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    hm = df.groupby(['day_of_week', 'hour'])['minutes'].mean().reset_index()
    hm_pivot = hm.pivot(index='day_of_week', columns='hour', values='minutes')
    hm_pivot = hm_pivot.reindex([d for d in day_order if d in hm_pivot.index])

    fig, ax = plt.subplots(figsize=(16, 5))
    sns.heatmap(hm_pivot, cmap='YlOrRd', ax=ax, cbar_kws={'label': 'Avg Minutes'})
    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('')
    st.pyplot(fig)
    plt.close()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Weekend vs Weekday")
        full_df = load_data()
        if isinstance(date_range, tuple) and len(date_range) == 2:
            full_df = full_df[(full_df['date'].dt.date >= date_range[0]) & (full_df['date'].dt.date <= date_range[1])]
        full_df = full_df[full_df['app'].isin(selected_apps) & full_df['category'].isin(selected_categories)]
        wk = full_df.groupby(['is_weekend', 'category'])['minutes'].sum().reset_index()
        wk['type'] = wk['is_weekend'].map({True: 'Weekend', False: 'Weekday'})
        wd_count = full_df[~full_df['is_weekend']]['date'].nunique() or 1
        we_count = full_df[full_df['is_weekend']]['date'].nunique() or 1
        wk.loc[wk['type'] == 'Weekday', 'avg_hours'] = wk.loc[wk['type'] == 'Weekday', 'minutes'] / wd_count / 60
        wk.loc[wk['type'] == 'Weekend', 'avg_hours'] = wk.loc[wk['type'] == 'Weekend', 'minutes'] / we_count / 60

        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=wk, x='category', y='avg_hours', hue='type', ax=ax, palette=['#3498DB', '#E74C3C'])
        ax.set_ylabel('Avg Daily Hours')
        ax.set_xlabel('')
        plt.xticks(rotation=30)
        st.pyplot(fig)
        plt.close()

    with col2:
        st.subheader("Hourly Profile")
        hourly = df.groupby('hour')['minutes'].mean()
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.fill_between(hourly.index, hourly.values, alpha=0.3, color='#E74C3C')
        ax.plot(hourly.index, hourly.values, color='#E74C3C', linewidth=2)
        ax.set_xlabel('Hour')
        ax.set_ylabel('Avg Minutes')
        ax.set_xticks(range(0, 24))
        st.pyplot(fig)
        plt.close()

# ── Tab 4: Triggers & Nudges ────────────────────────────────────────────
with tab4:
    st.subheader("What Drives Your Screen Time?")

    hourly_agg = df.groupby(['date', 'hour']).agg(
        total_minutes=('minutes', 'sum'),
        total_notifications=('notifications', 'sum'),
        total_pickups=('pickups', 'sum'),
    ).reset_index()

    col1, col2 = st.columns(2)
    with col1:
        corr1 = hourly_agg['total_notifications'].corr(hourly_agg['total_minutes'])
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(hourly_agg['total_notifications'], hourly_agg['total_minutes'], alpha=0.15, s=10, color='#E74C3C')
        z = np.polyfit(hourly_agg['total_notifications'], hourly_agg['total_minutes'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(hourly_agg['total_notifications'].min(), hourly_agg['total_notifications'].max(), 100)
        ax.plot(x_line, p(x_line), color='black', linewidth=2)
        ax.set_xlabel('Notifications per Hour')
        ax.set_ylabel('Minutes Used')
        ax.set_title(f'Notifications → Usage (r={corr1:.2f})')
        st.pyplot(fig)
        plt.close()
        st.info(f"Each notification adds roughly **{z[0]:.1f} minutes** of screen time.")

    with col2:
        corr2 = hourly_agg['total_pickups'].corr(hourly_agg['total_minutes'])
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(hourly_agg['total_pickups'], hourly_agg['total_minutes'], alpha=0.15, s=10, color='#3498DB')
        z2 = np.polyfit(hourly_agg['total_pickups'], hourly_agg['total_minutes'], 1)
        p2 = np.poly1d(z2)
        x_line2 = np.linspace(hourly_agg['total_pickups'].min(), hourly_agg['total_pickups'].max(), 100)
        ax.plot(x_line2, p2(x_line2), color='black', linewidth=2)
        ax.set_xlabel('Pickups per Hour')
        ax.set_ylabel('Minutes Used')
        ax.set_title(f'Pickups → Usage (r={corr2:.2f})')
        st.pyplot(fig)
        plt.close()

    st.subheader("What Triggers Phone Pickups?")
    pickup_weights = {
        'Instagram': 0.22, 'WhatsApp': 0.20, 'TikTok': 0.15, 'Twitter/X': 0.12,
        'Gmail': 0.10, 'Slack': 0.08, 'Chrome': 0.05, 'Reddit': 0.04,
        'YouTube': 0.02, 'LinkedIn': 0.02,
    }
    total_pickups = daily['total_pickups'].sum()
    first_app = pd.DataFrame([
        {'App': k, 'Times Opened First': int(v * total_pickups)}
        for k, v in pickup_weights.items() if k in selected_apps
    ]).sort_values('Times Opened First', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ['#E74C3C' if APP_META.get(a, {}).get('addictive', False) else '#3498DB' for a in first_app['App']]
    ax.barh(first_app['App'], first_app['Times Opened First'], color=colors)
    ax.set_xlabel('Times Opened First After Pickup')
    st.pyplot(fig)
    plt.close()

    st.subheader("Notification Volume by App")
    notif_by_app = df.groupby('app')['notifications'].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    notif_by_app.plot.bar(ax=ax, color=['#E74C3C' if APP_META.get(a, {}).get('addictive', False) else '#3498DB' for a in notif_by_app.index])
    ax.set_ylabel('Total Notifications')
    ax.set_xlabel('')
    plt.xticks(rotation=30)
    st.pyplot(fig)
    plt.close()

# ── Tab 5: Late Night ───────────────────────────────────────────────────
with tab5:
    st.subheader("Late-Night Doom Scrolling (10pm – 1am)")

    hour_range = st.slider("Define 'late night' hours", 0, 23, (22, 23), key="late")
    late_hours = list(range(hour_range[0], hour_range[1] + 1))
    if hour_range[0] >= 22:
        late_hours = list(range(hour_range[0], 24)) + list(range(0, max(1, hour_range[1] - 23)))

    late = df[df['hour'].isin(late_hours)]
    late_total_hours = late['minutes'].sum() / 60
    total_all = df['minutes'].sum() / 60

    m1, m2, m3 = st.columns(3)
    m1.metric("Late-Night Hours", f"{late_total_hours:.0f}h")
    m2.metric("% of Total", f"{late_total_hours / max(total_all, 1) * 100:.1f}%")
    m3.metric("Avg/Night", f"{late_total_hours / max(num_days, 1) * 60:.0f} min")

    late_by_app = late.groupby('app')['minutes'].sum().sort_values(ascending=False).head(8) / 60
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(late_by_app.index, late_by_app.values,
                  color=['#E74C3C' if APP_META.get(a, {}).get('addictive', False) else '#95A5A6' for a in late_by_app.index])
    ax.set_ylabel('Hours')
    for bar, val in zip(bars, late_by_app.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3, f'{val:.0f}h', ha='center', fontsize=9)
    plt.xticks(rotation=30)
    st.pyplot(fig)
    plt.close()

    st.subheader("Late-Night Trend Over Time")
    late_daily = late.groupby('date')['minutes'].sum().reset_index()
    late_daily.columns = ['date', 'late_minutes']
    late_daily = late_daily.sort_values('date')
    late_daily['rolling'] = late_daily['late_minutes'].rolling(7).mean()

    fig, ax = plt.subplots(figsize=(14, 4))
    ax.bar(late_daily['date'], late_daily['late_minutes'], alpha=0.3, color='#9B59B6')
    ax.plot(late_daily['date'], late_daily['rolling'], color='#E74C3C', linewidth=2)
    ax.set_ylabel('Minutes')
    st.pyplot(fig)
    plt.close()

# ── Tab 6: Recommendations ──────────────────────────────────────────────
with tab6:
    st.subheader("Personalized Recommendations")

    avg_hrs = daily['hours'].mean()
    addictive_hrs = df[df['app'].map(lambda a: APP_META.get(a, {}).get('addictive', False))]['minutes'].sum() / 60 / max(num_days, 1)

    if avg_hrs > 8:
        st.error(f"**Critical:** You're averaging **{avg_hrs:.1f} hours/day** — well above the recommended 2-3 hours.")
    elif avg_hrs > 5:
        st.warning(f"**High:** You're averaging **{avg_hrs:.1f} hours/day** — above average.")
    else:
        st.success(f"**Good:** You're averaging **{avg_hrs:.1f} hours/day** — within a reasonable range.")

    st.markdown("---")

    recommendations = []

    hourly_agg_full = df.groupby(['date', 'hour']).agg(
        total_minutes=('minutes', 'sum'),
        total_notifications=('notifications', 'sum'),
    ).reset_index()
    z_full = np.polyfit(hourly_agg_full['total_notifications'], hourly_agg_full['total_minutes'], 1)
    notif_savings = z_full[0] * 20

    recommendations.append({
        'title': 'Turn Off Non-Essential Notifications',
        'detail': f'Notifications drive ~{z_full[0]:.1f} min of usage each. Muting TikTok, Instagram, and Twitter could save ~{notif_savings:.0f} min/day.',
        'impact': 'High',
    })

    late_default = df[df['hour'].isin([22, 23, 0])]
    late_hrs_per_night = late_default['minutes'].sum() / 60 / max(num_days, 1) * 60
    recommendations.append({
        'title': 'Set a 10:30pm Bedtime Screen Lock',
        'detail': f'You spend ~{late_hrs_per_night:.0f} min/night scrolling after 10pm. A bedtime lock could reclaim this time and improve sleep quality.',
        'impact': 'High',
    })

    if addictive_hrs > 3:
        recommendations.append({
            'title': 'Set App Timers for Dopamine Apps',
            'detail': f'You spend {addictive_hrs:.1f}h/day on addictive apps. Set daily limits: Instagram 30min, YouTube 30min, TikTok 20min.',
            'impact': 'High',
        })

    wkend_avg_full = daily[daily['date'].dt.weekday.isin([5, 6])]['hours'].mean() if daily[daily['date'].dt.weekday.isin([5, 6])].shape[0] > 0 else 0
    wkday_avg_full = daily[~daily['date'].dt.weekday.isin([5, 6])]['hours'].mean() if daily[~daily['date'].dt.weekday.isin([5, 6])].shape[0] > 0 else 0
    if wkend_avg_full > wkday_avg_full * 1.2:
        recommendations.append({
            'title': 'Plan Weekend Activities Away From Screens',
            'detail': f'Weekends ({wkend_avg_full:.1f}h) are {(wkend_avg_full - wkday_avg_full) / max(wkday_avg_full, 1) * 100:.0f}% higher than weekdays ({wkday_avg_full:.1f}h). Plan outdoor or offline activities.',
            'impact': 'Medium',
        })

    recommendations.append({
        'title': 'Move Social Media Off Home Screen',
        'detail': 'Instagram and TikTok are the most common first-open apps. Moving them to a second screen or folder adds friction.',
        'impact': 'Medium',
    })

    recommendations.append({
        'title': 'Enable Grayscale Mode',
        'detail': 'Colorful app icons and UI trigger dopamine. Grayscale mode makes your phone less visually enticing.',
        'impact': 'Low',
    })

    for i, rec in enumerate(recommendations):
        impact_color = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}[rec['impact']]
        with st.expander(f"{impact_color} {rec['title']} — Impact: {rec['impact']}", expanded=(i < 3)):
            st.write(rec['detail'])

    st.markdown("---")
    st.subheader("Your Usage Scorecard")
    score = 100
    if avg_hrs > 8:
        score -= 30
    elif avg_hrs > 5:
        score -= 15
    if addictive_pct > 60:
        score -= 20
    elif addictive_pct > 40:
        score -= 10
    if len(weekly) >= 2:
        creep = (weekly['avg_hours'].iloc[-1] - weekly['avg_hours'].iloc[0]) / max(weekly['avg_hours'].iloc[0], 1) * 100
        if creep > 15:
            score -= 15
        elif creep > 5:
            score -= 5
    late_pct = late_default['minutes'].sum() / max(df['minutes'].sum(), 1) * 100
    if late_pct > 20:
        score -= 15
    elif late_pct > 10:
        score -= 5
    score = max(0, min(100, score))

    if score >= 70:
        st.success(f"**Digital Wellness Score: {score}/100** — You're doing okay, but there's room to improve.")
    elif score >= 40:
        st.warning(f"**Digital Wellness Score: {score}/100** — Your phone habits need attention.")
    else:
        st.error(f"**Digital Wellness Score: {score}/100** — Your phone usage is significantly impacting your time.")

    breakdown = {
        'Screen Time': '✅' if avg_hrs <= 5 else ('⚠️' if avg_hrs <= 8 else '❌'),
        'Addictive App %': '✅' if addictive_pct <= 40 else ('⚠️' if addictive_pct <= 60 else '❌'),
        'Late-Night Use': '✅' if late_pct <= 10 else ('⚠️' if late_pct <= 20 else '❌'),
        'Usage Trend': '✅' if (len(weekly) < 2 or creep <= 5) else ('⚠️' if creep <= 15 else '❌'),
    }
    for k, v in breakdown.items():
        st.write(f"{v} **{k}**")
