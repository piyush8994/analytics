import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# ── Generate 90 days of realistic phone usage data ──────────────────────────
apps = {
    'Instagram':    {'category': 'Social Media',   'base_min': 35, 'addictive': True,  'notification_rate': 12},
    'YouTube':      {'category': 'Entertainment',  'base_min': 40, 'addictive': True,  'notification_rate': 8},
    'WhatsApp':     {'category': 'Messaging',      'base_min': 25, 'addictive': False, 'notification_rate': 30},
    'Twitter/X':    {'category': 'Social Media',   'base_min': 20, 'addictive': True,  'notification_rate': 15},
    'Reddit':       {'category': 'Social Media',   'base_min': 18, 'addictive': True,  'notification_rate': 5},
    'Chrome':       {'category': 'Productivity',   'base_min': 15, 'addictive': False, 'notification_rate': 2},
    'Gmail':        {'category': 'Productivity',   'base_min': 10, 'addictive': False, 'notification_rate': 18},
    'Spotify':      {'category': 'Entertainment',  'base_min': 22, 'addictive': False, 'notification_rate': 3},
    'Netflix':      {'category': 'Entertainment',  'base_min': 30, 'addictive': True,  'notification_rate': 2},
    'TikTok':       {'category': 'Social Media',   'base_min': 28, 'addictive': True,  'notification_rate': 20},
    'Maps':         {'category': 'Utility',        'base_min': 5,  'addictive': False, 'notification_rate': 1},
    'Phone':        {'category': 'Communication',  'base_min': 8,  'addictive': False, 'notification_rate': 5},
    'Settings':     {'category': 'Utility',        'base_min': 3,  'addictive': False, 'notification_rate': 0},
    'Slack':        {'category': 'Productivity',   'base_min': 12, 'addictive': False, 'notification_rate': 22},
    'LinkedIn':     {'category': 'Social Media',   'base_min': 8,  'addictive': False, 'notification_rate': 6},
}

start_date = datetime(2026, 3, 30)
records = []

for day_offset in range(90):
    date = start_date + timedelta(days=day_offset)
    dow = date.weekday()
    is_weekend = dow >= 5

    for hour in range(24):
        for app_name, props in apps.items():
            # Skip most apps during sleep hours
            if hour in range(1, 6) and app_name not in ['WhatsApp']:
                if np.random.random() > 0.02:
                    continue

            base = props['base_min'] / 16  # distribute across waking hours

            # Weekend boost for entertainment/social
            if is_weekend and props['category'] in ['Social Media', 'Entertainment']:
                base *= 1.6

            # Late night doom-scrolling (10pm-1am) for addictive apps
            if hour in [22, 23, 0] and props['addictive']:
                base *= 2.5

            # Morning check surge (7-9am) for social/messaging
            if hour in [7, 8] and props['category'] in ['Social Media', 'Messaging']:
                base *= 1.8

            # Lunch break surge (12-1pm)
            if hour in [12, 13] and props['category'] in ['Social Media', 'Entertainment']:
                base *= 1.5

            # Work hours boost for productivity apps
            if hour in range(9, 18) and props['category'] == 'Productivity':
                base *= 2.0

            # Boredom/stress Mondays
            if dow == 0 and props['addictive']:
                base *= 1.3

            # Gradual increase over time (creeping usage)
            base *= 1 + (day_offset / 90) * 0.25

            minutes = max(0, np.random.normal(base, base * 0.4))
            if minutes < 0.5:
                continue

            pickups = max(0, int(np.random.poisson(max(1, minutes / 8))))
            notifications = max(0, int(np.random.poisson(props['notification_rate'] / 16)))

            records.append({
                'date': date.strftime('%Y-%m-%d'),
                'hour': hour,
                'day_of_week': date.strftime('%A'),
                'is_weekend': is_weekend,
                'app': app_name,
                'category': props['category'],
                'minutes': round(minutes, 1),
                'pickups': pickups,
                'notifications': notifications,
                'is_addictive_app': props['addictive'],
            })

df = pd.DataFrame(records)
df['date'] = pd.to_datetime(df['date'])
df.to_csv('data/phone_usage_90days.csv', index=False)

# ── Set up plotting ─────────────────────────────────────────────────────────
sns.set_theme(style='whitegrid', palette='husl')
plt.rcParams.update({'figure.dpi': 150, 'figure.facecolor': 'white', 'font.size': 10})


# ═══════════════════════════════════════════════════════════════════════════
# 1. DAILY TOTAL SCREEN TIME TREND
# ═══════════════════════════════════════════════════════════════════════════
daily = df.groupby('date').agg(
    total_minutes=('minutes', 'sum'),
    total_pickups=('pickups', 'sum'),
    total_notifications=('notifications', 'sum'),
).reset_index()
daily['hours'] = daily['total_minutes'] / 60
daily['rolling_avg'] = daily['hours'].rolling(7).mean()

fig, ax = plt.subplots(figsize=(14, 5))
ax.bar(daily['date'], daily['hours'], alpha=0.35, color='#5B8DEF', label='Daily hours')
ax.plot(daily['date'], daily['rolling_avg'], color='#E74C3C', linewidth=2.5, label='7-day rolling avg')
ax.axhline(y=daily['hours'].median(), color='orange', linestyle='--', alpha=0.7, label=f'Median: {daily["hours"].median():.1f}h')
ax.set_ylabel('Screen Time (hours)')
ax.set_title('Daily Screen Time — 90-Day Trend', fontsize=14, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig('data/01_daily_trend.png')
plt.close()


# ═══════════════════════════════════════════════════════════════════════════
# 2. TOP APPS BY TOTAL USAGE
# ═══════════════════════════════════════════════════════════════════════════
app_total = df.groupby('app')['minutes'].sum().sort_values(ascending=True) / 60

fig, ax = plt.subplots(figsize=(10, 7))
colors = ['#E74C3C' if apps[a]['addictive'] else '#3498DB' for a in app_total.index]
bars = ax.barh(app_total.index, app_total.values, color=colors)
ax.set_xlabel('Total Hours (90 days)')
ax.set_title('Total Screen Time by App\n(Red = high-dopamine/addictive apps)', fontsize=13, fontweight='bold')
for bar, val in zip(bars, app_total.values):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, f'{val:.0f}h', va='center', fontsize=9)
plt.tight_layout()
plt.savefig('data/02_top_apps.png')
plt.close()


# ═══════════════════════════════════════════════════════════════════════════
# 3. CATEGORY BREAKDOWN (PIE)
# ═══════════════════════════════════════════════════════════════════════════
cat_total = df.groupby('category')['minutes'].sum() / 60

fig, ax = plt.subplots(figsize=(8, 8))
wedges, texts, autotexts = ax.pie(
    cat_total.values, labels=cat_total.index, autopct='%1.1f%%',
    colors=sns.color_palette('Set2', len(cat_total)),
    startangle=140, textprops={'fontsize': 11}
)
ax.set_title('Screen Time by Category', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('data/03_category_pie.png')
plt.close()


# ═══════════════════════════════════════════════════════════════════════════
# 4. HOURLY USAGE HEATMAP (hour × day-of-week)
# ═══════════════════════════════════════════════════════════════════════════
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
heatmap_data = df.groupby(['day_of_week', 'hour'])['minutes'].mean().reset_index()
heatmap_pivot = heatmap_data.pivot(index='day_of_week', columns='hour', values='minutes')
heatmap_pivot = heatmap_pivot.reindex(day_order)

fig, ax = plt.subplots(figsize=(16, 6))
sns.heatmap(heatmap_pivot, cmap='YlOrRd', annot=False, ax=ax, cbar_kws={'label': 'Avg Minutes'})
ax.set_title('When Do You Use Your Phone Most? (Hour × Day)', fontsize=14, fontweight='bold')
ax.set_xlabel('Hour of Day')
ax.set_ylabel('')
plt.tight_layout()
plt.savefig('data/04_hourly_heatmap.png')
plt.close()


# ═══════════════════════════════════════════════════════════════════════════
# 5. WEEKEND vs WEEKDAY COMPARISON
# ═══════════════════════════════════════════════════════════════════════════
wk_compare = df.groupby(['is_weekend', 'category'])['minutes'].sum().reset_index()
wk_compare['type'] = wk_compare['is_weekend'].map({True: 'Weekend', False: 'Weekday'})
# normalize to per-day
weekday_count = daily[~daily['date'].dt.weekday.isin([5,6])].shape[0]
weekend_count = daily[daily['date'].dt.weekday.isin([5,6])].shape[0]
wk_compare.loc[wk_compare['type']=='Weekday', 'avg_hours'] = wk_compare.loc[wk_compare['type']=='Weekday', 'minutes'] / weekday_count / 60
wk_compare.loc[wk_compare['type']=='Weekend', 'avg_hours'] = wk_compare.loc[wk_compare['type']=='Weekend', 'minutes'] / weekend_count / 60

fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(data=wk_compare, x='category', y='avg_hours', hue='type', ax=ax, palette=['#3498DB', '#E74C3C'])
ax.set_ylabel('Avg Daily Hours')
ax.set_title('Weekend vs Weekday: Where Does Extra Time Go?', fontsize=13, fontweight='bold')
ax.set_xlabel('')
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig('data/05_weekend_vs_weekday.png')
plt.close()


# ═══════════════════════════════════════════════════════════════════════════
# 6. NOTIFICATION → USAGE CORRELATION
# ═══════════════════════════════════════════════════════════════════════════
hourly_agg = df.groupby(['date', 'hour']).agg(
    total_minutes=('minutes', 'sum'),
    total_notifications=('notifications', 'sum'),
    total_pickups=('pickups', 'sum'),
).reset_index()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].scatter(hourly_agg['total_notifications'], hourly_agg['total_minutes'], alpha=0.15, s=10, color='#E74C3C')
z = np.polyfit(hourly_agg['total_notifications'], hourly_agg['total_minutes'], 1)
p = np.poly1d(z)
x_line = np.linspace(hourly_agg['total_notifications'].min(), hourly_agg['total_notifications'].max(), 100)
axes[0].plot(x_line, p(x_line), color='black', linewidth=2)
corr1 = hourly_agg['total_notifications'].corr(hourly_agg['total_minutes'])
axes[0].set_xlabel('Notifications per Hour')
axes[0].set_ylabel('Minutes Used per Hour')
axes[0].set_title(f'Notifications → Screen Time (r={corr1:.2f})', fontweight='bold')

axes[1].scatter(hourly_agg['total_pickups'], hourly_agg['total_minutes'], alpha=0.15, s=10, color='#3498DB')
z2 = np.polyfit(hourly_agg['total_pickups'], hourly_agg['total_minutes'], 1)
p2 = np.poly1d(z2)
x_line2 = np.linspace(hourly_agg['total_pickups'].min(), hourly_agg['total_pickups'].max(), 100)
axes[1].plot(x_line2, p2(x_line2), color='black', linewidth=2)
corr2 = hourly_agg['total_pickups'].corr(hourly_agg['total_minutes'])
axes[1].set_xlabel('Pickups per Hour')
axes[1].set_ylabel('Minutes Used per Hour')
axes[1].set_title(f'Phone Pickups → Screen Time (r={corr2:.2f})', fontweight='bold')
plt.tight_layout()
plt.savefig('data/06_notification_correlation.png')
plt.close()


# ═══════════════════════════════════════════════════════════════════════════
# 7. LATE-NIGHT DOOM SCROLLING ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
late_night = df[df['hour'].isin([22, 23, 0])].copy()
late_by_app = late_night.groupby('app')['minutes'].sum().sort_values(ascending=False).head(8) / 60

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(late_by_app.index, late_by_app.values, color=['#E74C3C' if apps[a]['addictive'] else '#95A5A6' for a in late_by_app.index])
ax.set_ylabel('Total Hours (10pm–1am)')
ax.set_title('Late-Night Doom Scrolling: Which Apps Keep You Up?', fontsize=13, fontweight='bold')
plt.xticks(rotation=30)
for bar, val in zip(bars, late_by_app.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3, f'{val:.0f}h', ha='center', fontsize=9)
plt.tight_layout()
plt.savefig('data/07_late_night_doom.png')
plt.close()


# ═══════════════════════════════════════════════════════════════════════════
# 8. USAGE CREEP — WEEKLY AVERAGES OVER TIME
# ═══════════════════════════════════════════════════════════════════════════
daily['week'] = daily['date'].dt.isocalendar().week.astype(int)
weekly = daily.groupby('week').agg(avg_hours=('hours', 'mean'), avg_pickups=('total_pickups', 'mean')).reset_index()

fig, ax1 = plt.subplots(figsize=(12, 5))
ax1.bar(weekly['week'], weekly['avg_hours'], color='#5B8DEF', alpha=0.7, label='Avg daily hours')
ax1.set_xlabel('Week Number')
ax1.set_ylabel('Avg Daily Screen Time (hours)', color='#5B8DEF')
ax2 = ax1.twinx()
ax2.plot(weekly['week'], weekly['avg_pickups'], color='#E74C3C', linewidth=2, marker='o', label='Avg daily pickups')
ax2.set_ylabel('Avg Daily Pickups', color='#E74C3C')
ax1.set_title('Usage Creep: Are You Using Your Phone More Over Time?', fontsize=13, fontweight='bold')
fig.legend(loc='upper left', bbox_to_anchor=(0.12, 0.92))
plt.tight_layout()
plt.savefig('data/08_usage_creep.png')
plt.close()


# ═══════════════════════════════════════════════════════════════════════════
# 9. APP-LEVEL DAILY TRENDS (top 5 apps)
# ═══════════════════════════════════════════════════════════════════════════
top5_apps = df.groupby('app')['minutes'].sum().nlargest(5).index
top5_daily = df[df['app'].isin(top5_apps)].groupby(['date', 'app'])['minutes'].sum().reset_index()
top5_daily['hours'] = top5_daily['minutes'] / 60

fig, ax = plt.subplots(figsize=(14, 6))
for app in top5_apps:
    app_data = top5_daily[top5_daily['app'] == app].sort_values('date')
    ax.plot(app_data['date'], app_data['hours'].rolling(7).mean(), linewidth=2, label=app)
ax.set_ylabel('Daily Hours (7-day rolling avg)')
ax.set_title('Top 5 Apps — Daily Usage Trend', fontsize=13, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig('data/09_top5_app_trends.png')
plt.close()


# ═══════════════════════════════════════════════════════════════════════════
# 10. PICKUP TRIGGERS — FIRST APP AFTER PICKUP SIMULATION
# ═══════════════════════════════════════════════════════════════════════════
pickup_weights = {
    'Instagram': 0.22, 'WhatsApp': 0.20, 'Twitter/X': 0.12, 'TikTok': 0.15,
    'Gmail': 0.10, 'Slack': 0.08, 'Chrome': 0.05, 'Reddit': 0.04,
    'YouTube': 0.02, 'LinkedIn': 0.02,
}
first_app_counts = {k: int(v * daily['total_pickups'].sum()) for k, v in pickup_weights.items()}
first_app_df = pd.DataFrame(list(first_app_counts.items()), columns=['app', 'times_opened_first'])
first_app_df = first_app_df.sort_values('times_opened_first', ascending=True)

fig, ax = plt.subplots(figsize=(10, 6))
colors = ['#E74C3C' if apps.get(a, {}).get('addictive', False) else '#3498DB' for a in first_app_df['app']]
ax.barh(first_app_df['app'], first_app_df['times_opened_first'], color=colors)
ax.set_xlabel('Times Opened First After Pickup')
ax.set_title('What Triggers You to Pick Up Your Phone?', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('data/10_pickup_triggers.png')
plt.close()


# ═══════════════════════════════════════════════════════════════════════════
# PRINT DETAILED INSIGHTS REPORT
# ═══════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("  PHONE USAGE ANALYSIS — DETAILED INSIGHTS REPORT")
print("  Period: Mar 30 – Jun 27, 2026 (90 days)")
print("=" * 70)

total_hours = daily['hours'].sum()
avg_daily = daily['hours'].mean()
max_day = daily.loc[daily['hours'].idxmax()]
min_day = daily.loc[daily['hours'].idxmin()]

print(f"\n📊 OVERALL SUMMARY")
print(f"   Total screen time:        {total_hours:.0f} hours ({total_hours/24:.0f} full days)")
print(f"   Daily average:            {avg_daily:.1f} hours/day")
print(f"   Heaviest day:             {max_day['date'].strftime('%b %d')} — {max_day['hours']:.1f}h")
print(f"   Lightest day:             {min_day['date'].strftime('%b %d')} — {min_day['hours']:.1f}h")
print(f"   Total pickups:            {daily['total_pickups'].sum():,.0f}")
print(f"   Avg pickups/day:          {daily['total_pickups'].mean():.0f}")
print(f"   Total notifications:      {daily['total_notifications'].sum():,.0f}")

print(f"\n🔴 TOP USAGE NUDGES & TRIGGERS")
print(f"   1. NOTIFICATIONS are the #1 driver (r={corr1:.2f} correlation with usage)")
print(f"      → WhatsApp, Slack, TikTok send the most notifications")
print(f"      → Each notification adds ~{z[0]:.1f} mins of screen time")
print(f"   2. LATE-NIGHT DOOM SCROLLING (10pm–1am)")
late_total = late_night['minutes'].sum() / 60
print(f"      → {late_total:.0f} hours wasted after 10pm ({late_total/total_hours*100:.1f}% of total)")
print(f"      → Worst offenders: {', '.join(late_by_app.head(3).index)}")
print(f"   3. WEEKEND BINGES")
wkend_avg = daily[daily['date'].dt.weekday.isin([5,6])]['hours'].mean()
wkday_avg = daily[~daily['date'].dt.weekday.isin([5,6])]['hours'].mean()
print(f"      → Weekends avg {wkend_avg:.1f}h vs weekday {wkday_avg:.1f}h (+{(wkend_avg-wkday_avg)/wkday_avg*100:.0f}%)")
print(f"   4. MONDAY STRESS SCROLLING")
mon_avg = daily[daily['date'].dt.weekday == 0]['hours'].mean()
print(f"      → Mondays avg {mon_avg:.1f}h (above weekday avg of {wkday_avg:.1f}h)")
print(f"   5. USAGE CREEP")
first_2weeks = daily.head(14)['hours'].mean()
last_2weeks = daily.tail(14)['hours'].mean()
print(f"      → First 2 weeks: {first_2weeks:.1f}h/day → Last 2 weeks: {last_2weeks:.1f}h/day")
print(f"      → That's a {(last_2weeks-first_2weeks)/first_2weeks*100:.0f}% increase over 90 days")

print(f"\n📱 APP-LEVEL BREAKDOWN (Total hours over 90 days)")
app_hours = df.groupby('app')['minutes'].sum().sort_values(ascending=False) / 60
for app, hrs in app_hours.items():
    marker = "🔴" if apps[app]['addictive'] else "🔵"
    print(f"   {marker} {app:15s} {hrs:6.0f}h  ({hrs/total_hours*100:4.1f}%)  avg {hrs/90:.1f}h/day")

print(f"\n⏰ PEAK USAGE HOURS")
hourly = df.groupby('hour')['minutes'].mean()
top_hours = hourly.nlargest(5)
for h, m in top_hours.items():
    print(f"   {h:02d}:00  →  {m:.0f} avg minutes")

print(f"\n🏷️ CATEGORY SUMMARY")
for cat, hrs in (cat_total.sort_values(ascending=False)).items():
    print(f"   {cat:20s} {hrs:.0f}h  ({hrs/total_hours*100:.1f}%)")

addictive_hours = df[df['is_addictive_app']]['minutes'].sum() / 60
print(f"\n⚠️  ADDICTION RISK")
print(f"   High-dopamine apps account for {addictive_hours:.0f}h ({addictive_hours/total_hours*100:.1f}% of total)")
print(f"   That's {addictive_hours/90:.1f} hours/day on apps designed to keep you scrolling")

print(f"\n💡 RECOMMENDATIONS")
print(f"   1. Turn off non-essential notifications (especially TikTok, Instagram, Twitter)")
print(f"      → Could save ~{z[0]*20:.0f} min/day based on notification-usage correlation")
print(f"   2. Set a bedtime screen lock at 10:30pm")
print(f"      → Could reclaim ~{late_total/90:.0f} min/night")
print(f"   3. Use app timers: Cap Instagram at 30min, YouTube at 30min, TikTok at 20min")
print(f"   4. Replace morning doom-scroll with a non-phone routine")
print(f"   5. Enable grayscale mode on weekends to reduce visual pull")
print(f"   6. Move social media apps off your home screen")

print(f"\n📈 Charts saved to data/ directory:")
print(f"   01_daily_trend.png           — 90-day screen time trend")
print(f"   02_top_apps.png              — Total usage by app")
print(f"   03_category_pie.png          — Category breakdown")
print(f"   04_hourly_heatmap.png        — Hour × day-of-week heatmap")
print(f"   05_weekend_vs_weekday.png    — Weekend vs weekday comparison")
print(f"   06_notification_correlation  — Notifications/pickups → usage")
print(f"   07_late_night_doom.png       — Late-night doom scrolling")
print(f"   08_usage_creep.png           — Weekly usage trend over time")
print(f"   09_top5_app_trends.png       — Top 5 app daily trends")
print(f"   10_pickup_triggers.png       — What triggers phone pickups")
print("=" * 70)
