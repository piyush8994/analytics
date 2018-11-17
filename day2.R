#create Vectors to be combined into DF
(rollno = 1:30)
(sname = paste('student',1:30,sep=''))
(gender = sample(c('M','F'), size=30, replace=T, prob=c(.7,.3)))
(marks1 = floor(rnorm(30,mean= 50,sd=10)))
(marks2 = ceiling(rnorm(30,40,5)))
(course = sample(c('BBA','MBA'), size=30, replace=T, prob=c(.5,.5)))
rollno; sname; gender
marks1 ; marks2; course

#create DF
df1= data.frame(rollno, sname, gender, marks1, marks2, course, stringsAsFactors = F)
df1$gender = factor(df1$gender)
df1$course = factor(df1$course)
str(df1)
head(df1)
install.packages('dplyr')
library(dplyr)
df1
df1%>%group_by(gender) %>% summarise(MeanM1 = mean(marks1), MeanM2 = mean(marks2),maxM2=max(marks2))
mean(marks2)

mtcars
mean(mtcars$mpg)
names(mtcars)
table(mtcars$gear) # for counting
table(mtcars$am,mtcars$cyl)
table(mtcars$cyl,mtcars$am,mtcars$vs)
#anothermethod for same thing
xtabs(~ am+cyl,data=mtcars)
#customised summary for multiple variables
mtcars %>% group_by(cyl, gear) %>% summarise(meanMPG = mean(mpg)) %>% arrange(meanMPG)
#decreasing order
mtcars %>% group_by(cyl, gear) %>% summarise(meanMPG = mean(mpg)) %>% arrange(desc(meanMPG))

#limit no. of rows
mtcars %>% select(mpg,wt) %>% head(n=7)
mtcars %>% select(mpg,wt) %>% slice(c(1,5,6))
#print alternate rows of a data set
mtcars %>% select(mpg,wt) %>% slice(seq(1,32,2))
mtcars %>% filter(mpg >25) %>% select(wt,hp,am,mpg)
#specific no of rows
mtcars %>% sample_n(3)
mtcars %>% sample_frac(.2)
