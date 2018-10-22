############ model_selection.R ############
# Author: Andrew Larkin
# Developed for Perry Hystad, Oregon State University
# Date created: September 18, 2018
# This script performs lasso varaible selection and incremental varaible buffer reduction for the NO2 LUR model.
# RMSE, AME, R2, Adj. R2, MB, and MAB are calculated for the final model.  The model coefficients, and minimum 
# p-value and percent variance explained for each variable and each region are also calculated.

####### load required packages #########
library(glmnet) # lasso regression

######################## helper functions #####################



# create a matrix in which the sign of protective variables "tr, ND, wa, us, and oe" are flipped.  
# flipping the sign of protective variables allows the lasso regression to restrict coefficients to 
# positive coefficients only: that is, a positive coefficient of an inverted protective value is 
# equivalent to a negative value before the sign of the variable was flipped
# INPUTS:
#    inData (dataframe) - matrix containing dataset 
# OuTPUTS:
#    inData (dataframe) - same matrix as input data, but with the signs of the protective
#                         variables flipped
posCoeffMatrix <- function(inData) {
  tempNames <- names(inData)
  endLength <- length(tempNames)
  switchList <- c("bL","ND","wa","pr","port_dist") # list of two characters that indicate protective variables
  # for each variable in the dataset, check if the variable is in the list of protective variables.
  # if the variable is protective, multiply the value by 1
  for(i in 1:endLength) {
    predType <- substr(tempNames[i],1,2)
    
    if(predType %in% switchList) {
      inData[,i] <- inData[,i]*-1
    }                     
  }
  return(inData)
  
} # end of posCoefMatrix



# create a multipanel image in ggplot2.  thanks to winston@stdout.org for providing this function.
# function was downloaded from http://www.cookbook-r.com/Graphs/Multiple_graphs_on_one_page_(ggplot2)/
multiplot <- function(..., plotlist=NULL, file, cols=1, layout=NULL, save) {
  library(grid)
  
  # Make a list from the ... arguments and plotlist
  plots <- c(list(...), plotlist)
  
  numPlots = length(plots)
  
  # If layout is NULL, then use 'cols' to determine layout
  if (is.null(layout)) {
    # Make the panel
    # ncol: Number of columns of plots
    # nrow: Number of rows needed, calculated from # of cols
    layout <- matrix(seq(1, cols * ceiling(numPlots/cols)),
                     ncol = cols, nrow = ceiling(numPlots/cols))
  }
  if(save!=FALSE) {
    ppi <- 300
    png(save, width=10*ppi, height=12*ppi,res=ppi)
  }
  if (numPlots==1) {
    print(plots[[1]])
    
  } else {
    # Set up the page
    grid.newpage()
    pushViewport(viewport(layout = grid.layout(nrow(layout), ncol(layout))))
    
    # Make each plot, in the correct location
    for (i in 1:numPlots) {
      # Get the i,j matrix positions of the regions that contain this subplot
      matchidx <- as.data.frame(which(layout == i, arr.ind = TRUE))
      print(plots[[i]], vp = viewport(layout.pos.row = matchidx$row,
                                      layout.pos.col = matchidx$col))
    }
  }
  
  if(save!=FALSE) {
    dev.off()
  }
} # end of multiplot




# identify the buffer sizes included in the variales in the input dataset.  This is done
# by removing the first two characters from each variable and converting the remaining 
# characters from characters to an integer value
# INPUTS:
#    inputData (dataframe) - matrix containing variables with buffer distances of interest 
# OuTPUTS:
#    buffDist (integer array) - array containing buffer distances, in ascending order
getBuffDistVec <- function(inputData) {
  buffDist <- rep(100,length(inputData)) # array that will contain output data
  # for each variable, extract the buffer distance from the variable name and conver to an
  # integer
  for(j in 1:length(inputData)) { 
    endP <- nchar(inputData[j]) -1 
    buffDist[j] <- as.numeric(substr(inputData[j],3,endP))
  } 
  buffDist <- buffDist[order(buffDist)] #order buffer distances in ascending order
  return(buffDist)
} # end of getBuffDistVec



# reduce buffers to only those that are more than x fold distance apart from one another
# INPUTS:
#    inputData (dataframe) - matrix containing variables with buffer distances of interest 
# OuTPUTS:
#    buffDist (integer array) - array containing buffer distances, in ascending order
reduceBuffList <- function(inputData,fold=3) {
  index = 1
  while(index<length(inputData)) {
    finishedVarCompare = FALSE
    while(finishedVarCompare == FALSE & index <length(inputData)) {
      if(inputData[index+1]/inputData[index] <= fold) {
        inputData <- inputData[-(index+1)]
      }
      else {
        finishedVarCompare=TRUE
      }
    }
    index = index +1
  }
  return(inputData)
} 



# reduce incremental variables within x fold values of the smallest vriable size
# INPUTS:
#    inCoef (float array) 
# OuTPUTS:
#    buffDist (integer array) - array containing buffer distances, in ascending order
reduceLassoModel <- function(inCoef,inPred,fold=5) {
  
  # create a vector of the first two characters for all variables
  bufferTypes <- c("aL","bL","bR","cL","cR","dR","eR","fR","wa","NDVI_14_16_") 
  
  a <- which(inCoef > 0) # identify which variables were selected by lasso regression
  b <- a[2:length(a)]-1 # remove the intercept from the model 
  subNames <- names(inPred)[b] # get the names of the variables selected by lasso regression
  finalList <- c()
  index <- 0
  
  # for each type of varaible, remove variables that are within 3 fold of a smaller variable
  for(index in 1:length(bufferTypes)) {
    tempData <- subNames[substr(subNames,1,2) %in% bufferTypes[index]] 
    
    # get the the distances for all buffers of the selected variable type
    if(length(tempData)>0) {
      cat(tempData)
      buffList <- getBuffDistVec(tempData)
      cat(buffList)
      reduced <- reduceBuffList(buffList,fold)
      m <- "m"
      reduced <- paste(bufferTypes[index],reduced,m,sep="")
      finalList <- c(finalList,reduced)
    }
  }
  
  otherVars <- subNames[substr(subNames,1,2) %in% bufferTypes == FALSE]
  finalList <- c(finalList,otherVars)
  return(finalList)
} # end of reduceLassoMode





# calculate the IQR for all variables in a matrix
# INPUTS:
#   inMatrix (dataframe) - variables for which IQR should be calculated
# OUTPUTS:
#   IQRVals (float array) - array of IQR values, in the same order as the 
#                           variables in inMatrix
calcIQR <- function(inMatrix) {
  IQRVals <- rep(0,length(inMatrix[1,]))
  for(i in 1:length(inMatrix[1,])) {
    IQRVals[i] <- IQR(inMatrix[,i])
  }
  return(IQRVals)
} # end of calcIQR



# remove variables that don't have enough measurements greater than 0 in the input dataset
# INPUTS:
#   inData (dataframe) - dataset containing predictor variables
#   minNumObs (int) - minimum number of observations that a dataset must contain
# OUTPUTS:
#   drops (string array) - names of the variables that don't have minNumObs number of observations in 
#   inData
restrictBuffsByNumObs <-function(inData,minNumObs) 
{
  attach(inData)
  vars <- names(inData)
  for(i in 1:length(vars)) 
  {
    currVar <- get(vars[i])
    nObs <- length(inData[currVar>0,1])
    if(minNumObs > nObs) 
    {
      drops <- c(drops,vars[i])
    }
  }
  detach(inData)
  return(drops)
}



calcPercentGreaterThan0 <-function(inData,minNumObs) 
{
  attach(inData)
  vars <- names(inData)
  totalObs <- length(inData[,1])
  percentObs <- rep(0,length(vars))
  for(i in 1:length(vars)) 
  {
    currVar <- get(vars[i])
    nObs <- length(inData[currVar>0,1])
    percentObs[i] <- nObs/totalObs
  }
  detach(inData)
  return(percentObs)
}


subsetRoads <- function(inData,keepsat = TRUE) {
  roadsLabel <- c("bR","cR","dR","eR","fR","alRds")
  keeps <- c()
  bufferDists <- c(50,100,250,500,750,1000,2000,3000,4000,5000,10000,15000,20000)
  for(i in 1:length(roadsLabel))
  {
    for(j in 1:length(bufferDists)) 
    {
      varName <- paste(roadsLabel[i],as.character(bufferDists[j]),"m", sep="")
      keeps <- c(keeps, varName)
    }
    
  }
  if(keepsat) keeps <- c(keeps,"sat_10_12")
  returnData <- inData[ , (names(inData) %in% keeps)]
  return(returnData)
}

subsetBuiltEnv <- function(inData,keepProtectors = TRUE,keepsat = TRUE)
{
  builtEnvLabel <- c("aL","bL","cL")
  if(keepProtectors) builtEnvLabel <- c(builtEnvLabel,"wa","NDVI_14_16_")
  keeps <- c()
  bufferDists <- c(50,100,250,500,750,1000,2000,3000,4000,5000,10000,15000,20000)
  for(i in 1:length(builtEnvLabel))
  {
    for(j in 1:length(bufferDists)) 
    {
      varName <- paste(builtEnvLabel[i],as.character(bufferDists[j]),"m", sep="")
      keeps <- c(keeps, varName)
    }
  }
  if(keepsat) keeps <- c(keeps,"sat_10_12")
  returnData <- inData[ , (names(inData) %in% keeps)]
  return(returnData)
}

dropNDVI <- function(inData)
{
  dropLabel <- c("NDVI_14_16_")
  drops <- c()
  bufferDists <- c(500,750,1000,2000,3000,4000,5000,10000,15000,20000)
  for(i in 1:length(dropLabel))
  {
    for(j in 1:length(bufferDists)) 
    {
      varName <- paste(dropLabel[i],as.character(bufferDists[j]),"m", sep="")
      drops <- c(drops, varName)
    }
  }
  returnData <- inData[ , !(names(inData) %in% drops)]
  return(returnData)
}



createLassoModel <- function(inData) 
{
  
  tempMat <- as.matrix(posCoeffMatrix(inData)) # reverse direction of protective variabless
  cvfit <- glmnet::cv.glmnet(tempMat,NO2_vals,type.measure = "mse",standardize=TRUE,alpha = 1,lower.limit=0) # perform lasso regression
  coefRaw <- coef(cvfit, s = "lambda.1se")
  keeps <- reduceLassoModel(coefRaw,inData,3)
  
  return(keeps)
}




# calculate and graph the partial R2 values for all variables and continental regions.
# INPUTS:
#    inData (dataframe) - data matrix containing predictor variables
#    inMonitor (float array) - array containing monitor measurements
calcPartialR2 <- function(inData, inMonitor) {
  
  tempMat <- as.matrix(inData)
  tempMonitor <- inMonitor
  partialR2 <- rep(0,length(inData))
  lmTotal <- lm(tempMonitor~tempMat)
  
  
  # claculate partial R2 for all variables in the dataset
  ssrTot <- sum(anova(lmTotal)$"Sum Sq"[1:2])
  sseTot <- anova(lmTotal)$"Sum Sq"[2]
  for(i in 1:length(inData)) {
    tempRemove <- names(inData)[i]
    tempData <- tempMat[ , !names(inData) %in% tempRemove]
    tempLm <- lm(tempMonitor~tempData)
    tempSSR <- anova(tempLm)$"Sum Sq"[1]
    tempSSE <- anova(tempLm)$"Sum Sq"[2]
    partialR2[i] <- (tempSSE - sseTot)/tempSSE
  }
  
  valMat <- round(partialR2*100,2)
  
  
  return(valMat)
  
} # end of graphPartialR2





# using an input dataset, randomly partition a training and testing dataset for cross-validation
# INPUTS:
#    inData (dataframe) - input dataset with predictor variables and air monitor measurements
#    sampProp (float) - value ranging from 0 to 1, indicating the proportion of data that should be partitioned to the training dataset
#    zoneVals (int vector) - indicates which zone the corresponding row of the input dataset belongs to
# OutPUTS:
#    returnData (dataframe) - input dataset with an indicator variable of whether each row belongs to the train or test partition
createTrainAndTest <- function(inData,sampProp) {
  
  smp_size <- floor(sampProp* nrow(inData)) # calculate the sample size for the training dataset
  cat(smp_size)
  train_ind <- sample(seq_len(nrow(inData)), size = smp_size) # randomly sample the entire dataset to make the training dataset
  train <- inData[train_ind, ]
  test <- inData[-train_ind, ]
  
  
  # create an indicator variable for whether a given sample (row in the dataset is a train or test point)
  train$ind <- rep(0,nrow(train))
  test$ind <- rep(1,nrow(test))
  
  returnData <- rbind(train,test) # combine the train and test dataset and return the result
  return(returnData)
} # end of createTrainAndTest






# perform leave 10% out cross-validation numRep number of times.  Return the root mean square, mean abs square, r-square,
# adjusted r-square, bias, and abs bias
# INPUTS:
#    inData (dataframe) - input data frame containing both the predictor and air monitor variables
#    numReps (int) - number of cross-validation repititions to perform
# OUTPUTS:
#    returnData (dataframe) - summary statistics of the cross-validation, for each region
crossValidation <- function(inPredictors,inMonitors,numReps,percTrain =0.8) {
  
  rmse <- ase <- rsq <- adjRsq <- bias <- absBias <- 0
  
  inPredictors$monitor <- inMonitors
  combinedData <- inPredictors
  
  p <- 1
  
  
  # for each cross-validation repitition
  for(i in 1:numReps) {
    cat(i) # print the repitition number to the screen
    cat("\n")
    
    trainInd <- createTrainAndTest(combinedData,percTrain) # create training and testing datasets
    
    # partition trainInd into training and test datasets based on the indicator variable ind ( 0 = 1, 1 = test)
    monitor <- trainInd$monitor 
    trainInd <- trainInd[ , !(names(trainInd) %in% c("monitor"))]
    trainSet <- subset(trainInd,ind == 0)
    trainMonitor <- subset(monitor,trainInd$ind == 0)
    testSet <- subset(trainInd,trainInd$ind == 1)
    testMonitor <- subset(monitor,trainInd$ind == 1)
    drops <- c("ind","monitor")
    trainSet <- trainSet[ , !(names(testSet) %in% drops)]
    testSet <- testSet[ , !(names(testSet) %in% drops)]
    
    lmModel <- lm(trainMonitor ~ aL2000m + NDVI_14_16_250m + sqTemp + logSat + sqAr + sqRa + sqPop  +  NDVI_14_16_250m  + logSat + sqTemp
                  , data = trainSet)
    coefRaw <- lmModel$coefficients
    
    testMat <- cbind(rep(1,nrow(testSet)),testSet)
    
    # create predictions for the test dataset based on the variables selected by the training dataset
    #pred <- as.vector(coefRaw[1:length(coefRaw)]%*%t(testMat))
    pred <- predict(lmModel,testSet)
    residuals <- testMonitor-pred
    n <- length(testMonitor)
    
    
    # calculate summary statistics 
    ase <- ase + mean(abs(residuals))
    sumSqErr <- sum(residuals^2)
    sumTot <- sum((testMonitor - mean(testMonitor))^2)
    rsq <- 1 - (sumSqErr/sumTot)
    rmse <- rmse + sqrt(mean(residuals^2))
    adjRsq <- adjRsq + 1 - (((1-rsq)*(n-1))/(n-p-1))
    absBias <- absBias + (100/length(residuals))*(sum(abs(residuals)/testMonitor))
    bias <- bias + (-100/length(residuals))*(sum(residuals/testMonitor))
    
    
  }
  
  ase <- ase/numReps
  rmse <- rmse/numReps
  absBias <- absBias/numReps
  bias <- bias/numReps
  adjRsq <- adjRsq/numReps
  
  returnData <- data.frame(rmse,ase,adjRsq,bias,absBias) # combine evaluation statistics into a dataframe to return as output
  return(returnData)
  
} # end of crossValidation




# create predictions for the test dataset based on the variables selected by the training dataset
#pred <- as.vector(coefRaw[1:length(coefRaw)]%*%t(testMat))
pred <- predict(lmModel,candidateModel)
residuals <- NO2_vals-pred
n <- length(NO2_vals)

# calculate summary statistics 
ase <- mean(abs(residuals))
sumSqErr <- sum(residuals^2)
sumTot <- sum((NO2_vals - mean(NO2_vals))^2)
rsq <- 1 - (sumSqErr/sumTot)
mse <- sqrt(mean(residuals^2))
n <- length(residuals)
p <- 1
adjRsq <- 1 - (((1-rsq)*(n-1))/(n-p-1))
absBias <- (100/length(residuals))*(sum(abs(residuals)/NO2_vals))
bias <- (-100/length(residuals))*(sum(residuals/NO2_vals))





################# main script #################

library(ggplot2)
library(glmnet)

#setwd("C:/users/larkinan/documents/Canada_NO2_LUR_14_16/Datasets")
setwd("C:/users/larkinan/documents/Canada_NO2_LUR_14_16/Datasets")


rawData <- read.csv("Canada_LUR_preprocessed_Sep17_18_v2.csv")



# setup data for processing
screenedData <- subset(rawData,elevation >-1)
NO2_vals <-  screenedData$meanNO2_2014_2016
drops <- c("meanNO2_2014_2016","NAPS.ID","percent.completeness_2013","percent.completeness_2014","percent.completeness_2015",
           "percent.completeness_2016","mean_2013","mean_2014","mean_2015","mean_2016", "numObs", "medYr", "minNO2", "meanNO2", "maxNO2", "stdDevNO2", "numMeas","FID","NAME","CONTINENT")
drops <- c(drops,"pr_14_16")
drops <- restrictBuffsByNumObs(screenedData,10)
exactMatrix <- screenedData[ , !(names(screenedData) %in% drops)]
exactMatrix <- dropNDVI(exactMatrix)
exactMatrix$logTemp <- log(exactMatrix$te_14_16+3)
exactMatrix$sqTemp <- (exactMatrix$te+3)^2
exactMatrix$logSat <- log(exactMatrix$sat_10_12)
exactMatrix$sqAr <- sqrt(exactMatrix$aR250m)
exactMatrix$sqRa <- sqrt(exactMatrix$Ra750m)
exactMatrix$sqPop <- sqrt(exactMatrix$PD20000)

tempMat <- as.matrix(posCoeffMatrix(exactMatrix)) # reverse direction of protective variabless
cvfit <- glmnet::cv.glmnet(tempMat,NO2_vals,type.measure = "mse",standardize=TRUE,alpha = 1,lower.limit=0) # perform lasso regression
coefRaw <- coef(cvfit, s = "lambda.1se")
keeps <- reduceLassoModel(coefRaw,exactMatrix,3)


createLassoModel(exactMatrix)




keeps <- c("aL2000m", "sqRa","sqAr","logSat","sqPop","sqTemp","NDVI_14_16_250m")
candidateModel <- exactMatrix[ , (names(exactMatrix) %in% keeps)]
calcPartialR2(candidateModel,NO2_vals)

lmModel <- lm(NO2_vals~ as.matrix(candidateModel))
predSub <- lmModel$fitted.values




crossValidation(candidateModel,NO2_vals,10000,0.8)








################## SUPPLEMENTAL SENSITIVITy ANALYSES ##############







############### test for sensitivity to percent monitor requirement ############


# at least 10 % of monitors have a value greater than 0
summary(lm(NO2_vals ~ aL2000m + aR250m  + te_14_16 + pr_14_16 + sat_10_12 + PD20000  +  NDVI_14_16_250m  
           , data = exactMatrix))


# at least 25% of monitors have a value greater than 0
summary(lm(NO2_vals ~ aL2000m  + Ra500m  + te_14_16 +pr_14_16+ sat_10_12 + PD20000  +  NDVI_14_16_250m 
           , data = exactMatrix))


# at least 50% of monitors have a value greater than 0
summary(lm(NO2_vals ~ aL2000m + aR1000m   + te_14_16 + pr_14_16 +
             sat_10_12 + PD20000 +  NDVI_14_16_250m,data=exactMatrix))



############### create models restricted to specific land use classes ###############


########### roads models ##############

# without satellite 
roadsData <- subsetRoads(exactMatrix,FALSE)
createLassoModel(roadsData)
linear_model <- lm(NO2_vals ~ eR2000m + dR15000m + alRds1000m, data = exactMatrix)

# with satellite 
roadsData <- subsetRoads(exactMatrix)
createLassoModel(roadsData)
linear_model <- lm(NO2_vals ~ eR2000m + sat_10_12 + dR15000m + alRds1000m, data = exactMatrix)


############ meteorological models ###########

# without satellite #
linear_model <- lm(NO2_vals ~ pr_14_16 + te_14_16, data = exactMatrix)

# with satellite #
linear_model <- lm(NO2_vals ~ pr_14_16 + te_14_16 + sat_10_12, data = exactMatrix)



############# built env models ##############

builtEnvData <- subsetBuiltEnv(exactMatrix)

# with protective variables and satellite
createLassoModel(builtEnvData,FALSE)
builtEnvData <- subsetBuiltEnv(exactMatrix,FALSE,TRUE)
linear_model <- lm(NO2_vals ~ aL2000m + aL15000m + cL5000m + sat_10_12 + NDVI_14_16_250m + NDVI_14_16_2000m + NDVI_14_16_10000m, data = exactMatrix)
builtEnvData <- subsetBuiltEnv(exactMatrix,FALSE)

# with satellite but not protective variables
createLassoModel(builtEnvData)
linear_model <- lm(NO2_vals ~ aL2000m + aL10000m + cL5000m + sat_10_12, data = exactMatrix)

# no satellite or protective variables 
builtEnvData <- subsetBuiltEnv(exactMatrix,FALSE,FALSE)
createLassoModel(builtEnvData)
linear_model <- lm(NO2_vals ~  aL2000m + aL15000m + cL5000m , data = exactMatrix)



########### end of ModelSelection.R ##########