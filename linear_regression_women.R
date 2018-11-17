#topics ----
#factors, env, import/export. package install
#rep, recode, split, partition, subset, loops, cast & melt
#missing values. duplicates, apply
#graphs - bar, multiple line, pie, box, corrgram

fit = lm(weight ~ height,data = women)
summary(fit)
range(women$height)
(ndata = data.frame(height = c(60.5, 70)))
(predictedwt = predict(fit, newdata = ndata))
cbind(ndata, predictedwt)
#use linear regression only to predict which are in input data range

resid(fit)
fitted(fit)
cbind(women,fitted(fit),resid(fit))
