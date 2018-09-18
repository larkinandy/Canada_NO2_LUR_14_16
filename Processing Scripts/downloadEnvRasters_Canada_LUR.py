############## downloadGreenspace.py ###################
# Author: Andrew Larkin
# Developed for Perry Hystad, Oregon State University
# Date last modified: June 5, 2018

# Description: this script downloads annual MODIS NDVI averages from Google Earth Engine.
# Annual averages range from 2003-2017.  NDVI values are based on TOA-scaled reflectance.  
# Multiple Landsat sensors are used to cover the time range as follows:

# Requirements:
#      Active Google Earth Engine account associated with the installed version of Python.  
#      ArcGIS with a liscence for the Spatial Analysis Library
# Tested and developed on:
#      Windows 10
#      Python 2.7
#      ArcGIS 10.3.2

################### setup ####################

# import modules 
import ee
import time
import datetime
import math
import os
import sys
import arcpy
import urllib2
import zipfile
import pandas as pd

# folder paths and variables
# the script, input csv need to be in the main folder.  Raster images should be downloaded to subfolders within the main folder
parentFolder = os.path.dirname(sys.argv[0]) + "/" 


inputCSVFile = parentFolder + "Stations2017_v3_csv_version.csv" # file with PURE location data
CSV_DICT = ['NAPS_ID','Lat_Decimal','Long_Decimal','StartYear'] # PURE attributes needed for the analysis
START_YEAR = 2016
END_YEAR = 2016

collectionName = 'LANDSAT/LC8_L1T_32DAY_NDVI' 

# environmental variables and checkout necessary extensions and libraries
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True
ee.Initialize()

# use a water mask to remove NDVI values over water bodies
waterMaskCollection = ee.ImageCollection("GLCF/GLS_WATER")
waterMask = waterMaskCollection.reduce(ee.Reducer.median())
waterMaskScreen = ee.Image(waterMask).neq(2) 

# reduce image catalog to a specific year and geographic region of interest
# INPUTS:
#    byear (str) - year of interest
#    filterBoundaries (ee.Geometry) - Google Earth Engine geometry object defining region of interest
#    collection (ee.ImageCollection) - Goolge Earth Engine image collection object containing rasters of interest
# OUTPUTS:
#    datedCollect (ee.ImageCollection ) - Google Earth Engine image collection containing filtered raster dataset
def filterCatalogSet(byear,filterBoundaries,collection):
    startDate = str(int(byear)) + "-01-01"
    endDate = str(byear) + "-12-31"    
    datedCollect = collection.filterDate(startDate,endDate)
    datedCollect = datedCollect.filterBounds(filterBoundaries)
    return(datedCollect)

# test if all raster images for all years for a specific location have been downloaded 
# INPUTS:
#   inputParams (dict)
#        startYear (int) - start year of data to download rasters for
#        endYear (int) - end year of data to download rasters for
#        randID (int) - random id for the community to identify exposures for
#   folderToTest (str) - full filepath to the folder to test
# OUTPUTS:
#   boolean - True if folder contains all raster images, false otherwise
def testComplete(inputParams,folderToTest):
    startYear = inputParams['startYear']
    endYear = inputParams['endYear']
    randID = inputParams['randID']
    startYear = inputParams['startYear']
    endYear = inputParams['endYear']
    randID = inputParams['randID']
    for year in range(startYear,endYear+1):
        yearFolder = folderToTest + str(year)
        zipFile = yearFolder + "/"+ str(randID) + ".zip"            
        if not(os.path.exists(zipFile)):
            return False
    return True

# download all raster images for a single location 
# INPUTS:
#   inputParams (dict)
#        startYear (int) - start year of data to download rasters for
#        endYear (int) - end year of data to download rasters for
#        randID (int) - random id for the community to identify exposures for
#   reducer (ee.reducer) - custom Google Earth Engine object
#   outputFolder (str) - full filepath to where rasters should be saved  
def downloadSinglePoint(inputParams, reducer,outputFolder):
    isComplete = testComplete(inputParams,outputFolder)
    if(isComplete):
        return True
    randID = inputParams['randID']
    latit = inputParams['lat']
    longit = inputParams['longit']
    startYear = inputParams['startYear']
    endYear = inputParams['endYear']
    
    
    
    padding = 0.51 # amount of padding around boundary to add to the raster
    filterBoundaries = ee.Geometry.Rectangle(longit + padding,
                                             latit + padding,
                                             longit - padding,
                                             latit - padding)  
    for year in range(startYear,endYear+1):
        yearFolder = outputFolder + str(year)
        zipFile = yearFolder + "/"+ str(randID) + ".zip"           
        download=False
        timeToSleep=2
        while download==False:       
            if not(os.path.exists(zipFile)):
                try:
                    download = downloadSingleRaster(year,yearFolder,filterBoundaries,reducer,zipFile,timeToSleep)
                except Exception as e:
                    print(str(e))
                finally:
                    time.sleep(timeToSleep)
            else:
                print(zipFile + " already exists, did you already download this raster?")      
                download=True

# download one raster
# INPUTS:
#    year (str) - year of raster coverage
#    yearFolder (str) - full filepath where image will be downloaded
#    filterBoundaries (ee.Geometry.Rectangle) - spatial exxtent of raster to download
#    reducer (ee.Reducer) - custom Google Earth Engine object - defines which type of summar stat to use (e.g. mean)
#    zipFile (str) - full filepath where the zipped raster should be written to 
# OUTPUTS:
#    True if raster download was successful, false otherwise
def downloadSingleRaster(year,yearFolder,filterBoundaries,reducer,zipFile,timeToSleep):      
    params = {'scale':'30'} # spatial resolution, in units of meters.  Finest possible reoslution for MODIS is 250m, for Landsat8 is 30m
    collection = ee.ImageCollection(collectionName)
    imageCatalog = filterCatalogSet(year,filterBoundaries,collection)
    screenedImg = imageCatalog.map(mapMask)
    reducedImage = screenedImg.reduce(reducer)
    clippedImage = reducedImage.clip(filterBoundaries)
    url = clippedImage.getDownloadURL(params)
    print("the url to download is " + url)    
    try:
        if(os.path.exists(yearFolder) == False):
            os.mkdir(yearFolder)        
        f = open(zipFile ,'wb')
        f.write(urllib2.urlopen(url,timeout= 10*6).read())
        f.close()    
        zip_ref = zipfile.ZipFile(zipFile, 'r')
        zip_ref.extractall(yearFolder)
        zip_ref.close()
        return(True)   
    except Exception as e:
        print(str(e))
        if(str(e) == "HTTP Error 400: Bad Request"):
            return(True)
        time.sleep(timeToSleep)
        timeToSleep = min(60,timeToSleep+10)
        print(timeToSleep)
        try:
            f.close()
        except Exception as e:
            print(e)
        if(os.path.exists(zipFile)):
            os.remove(zipFile)
        return(False)

# map an NDVI calculation and  mask function to apply to each image in the NDVI dataset
# Inputs:
#    image (Google Earth Engine image object) - raster image to apply the NDVI calculation
#    and mask function to
# Outputs:
#    image (Google Earth Engine image object) - NDVI values of the input image after applying
#    the cloud and water mask
def mapMask(image):
    #ndvi = ee.Image(image).select('NDVI')
    #fmaskVals = ee.Image(image).select('SummaryQA')
    validVals = [0,1]
    #screenedImg = ee.Image(fmaskVals).neq(-1)
    #screenedImg3 = ee.Image(fmaskVals).neq(2)
    #screenedImg4 = ee.Image(fmaskVals).neq(3)

    screenedImg = ee.Image(image).updateMask(waterMaskScreen)
    return screenedImg



# process downloaded NDVI raster so ArcGIS properly recognizes null values as "NULL"
# Inputs:
#    inputFolder (string) - folder containing .tif images to process
#    outputFolder (string) - folder containing input .tif images with NULL values 
#    recognizable by ArcGIS
def createRasters(inputFolder,outputFolder):
    filesToProcess = os.listdir(inputFolder)
    fileList = []
    # for each file in the folder, change exact 0 values to NULL
    for filename in filesToProcess:
        if(filename[len(filename)-3:len(filename)] == "tif"):
            fileList.append(filename)
    for filename in fileList:
        outSetNull = arcpy.sa.SetNull(inputFolder + filename, inputFolder + filename, "VALUE = 0")    
        outputName = outputFolder + filename[2:len(filename)-4] + "null"
        outSetNull.save(outputName.replace('.','')+ ".tif")

# get data from a single row of a pandas dataframe
# INPUTS:
#    rawData (pandas df) - contains raw data to read from
#    index (int) - row number to read
#    startYear (int) - first year of data coverage
#    endYear (int) - last year of data coverage
# OUTPUTS:
#    tempDict (dictionary)
#       randID (int) - id previously assigned randomly to row instance
#       lat (float) - latitude coordinate
#       longit (float) - longitude coordinate
#       startYear (int) - starting year of data coverage
#       endYear (int) - ending year of data coverage
def getRowData(rawData,index,startYear,endYear):
    tempRow = rawData.iloc[index]
    print(tempRow.head())
    tempRandID = int(tempRow[CSV_DICT[0]])
    tempLat = tempRow[CSV_DICT[1]]
    tempLong = tempRow[CSV_DICT[2]]
    tempDict = {'randID':tempRandID,'lat':tempLat,'longit':tempLong,'startYear':startYear,'endYear':endYear}
    return(tempDict)

# test all zipped files in an input folder for correctness and remove corrupted files
# INPUTS:
#    inputFolder (str) - folder containing zip files to test (and clean)
def cleanZip(inputFolder):
    candidateZips = os.listdir(inputFolder)
    for candidate in candidateZips:
        if(candidate[len(candidate)-3:len(candidate)] == "zip"):
            try:
                a = zipfile.ZipFile(inputFolder + "/" + candidate)
                if(len(a.namelist()))==0:
                    del(a)
                    os.remove(inputFolder + "/" + candidate)                    
            except:
                print("removing file " + candidate)
                os.remove(inputFolder + "/" + candidate)


# perform focal statistics on a single raster
# INPUTS:
#    inputRaster (str) - full filepath to the raster
#    numCells (int) - radius of the focal statistics, in number of cells
#    outputFile (str) - full filepath where the output focal statistics raster will be written
def focalStatsOnOneRaster(inputRaster,numCells, outputFile):
    outRaster = arcpy.sa.FocalStatistics(inputRaster, arcpy.sa.NbrCircle(numCells, "CELL"), "MEAN", "DATA")
    outRaster.save(outputFile)

# perform focal statistics on all rasters located within a given input folder
# INPUTS:
#    inputFolder (str) - folder where rasters to perform focal stats on are stored
#    numCells (int) - radius of the focal statistics, in number of cells
#    outputFolder (str) - full filepath where the output focal statistics raster will be written
def focalStatisticsAllRasters(inputFolder,numCells,outputFolder):
    candidateFiles = os.listdir(inputFolder)
    filesToProcess = []
    for candidateFile in candidateFiles:
        if(candidateFile[len(candidateFile)-3:len(candidateFile)] == "tif"):
            outputFile = outputFolder + "/" + candidateFile[0:len(candidateFile)-8] + ".tif"
            if not (os.path.exists(outputFile)):
                print(outputFile)
                focalStatsOnOneRaster(inputFolder + "/" + candidateFile, numCells,outputFile)
            else:
                print(outputFile + ' already exists')


# merge multiple rasters into a single mosaiced raster
# INPUTS:
#   inputFolder (str) - folder containing all rasters to merge
#   year (int) - year all rasters represent - used in mosaic filename
def mergeRasters(inputFolder,year):
    candidateFiles = os.listdir(inputFolder)
    filesToMerge = []
    for candidateFile in candidateFiles:
        if(candidateFile[len(candidateFile)-3:len(candidateFile)] == "tif"):
            filesToMerge.append(inputFolder + "/" + candidateFile)
    print(filesToMerge)
    
    arcpy.MosaicToNewRaster_management( 
        input_rasters=filesToMerge, output_location=parentFolder, 
        raster_dataset_name_with_extension="uNDVIx" + str(year) + ".tif", 
        coordinate_system_for_the_raster="", 
        pixel_type="32_BIT_FLOAT", cellsize="", 
        number_of_bands="1", 
        mosaic_method="MAXIMUM", 
        mosaic_colormap_mode="FIRST"
    )


#################### main function #############

# download all MODIS NDVI rasters for all years and all locations
# INPUTS:
#   rawData (dataframe) - pandas dataframe containing data read from csv
#   reducerType (str) - type of ee.Reducer to create: mean or max
#   unscreenedRasterFolder (str) - folder where downloaded rasters will be stored
#   startYear (int) - starting year of data coverage
#   endYear (int) - ending year of data coverage
def downloadNDVI_All_Years(rawData, reducerType,unscreenedRasterFolder,startYear,endYear):
    for i in range(startYear,endYear+1):
        if(os.path.exists(unscreenedRasterFolder + str(i))):
            cleanZip(unscreenedRasterFolder + str(i))
    if(reducerType=="MEAN"):
        reducer = ee.Reducer.mean()
    else:
        reducer = ee.Reducer.max()
    for index in range(1,rawData.count()[1]):    
        downloadSinglePoint(getRowData(rawData,index,startYear,endYear),reducer,unscreenedRasterFolder)
    
    

def main():
    rawData = pd.read_csv(inputCSVFile)
    #screenedRasterFolder = parentFolder + "screenedMean/"
    #unscreenedRasterFolder =parentFolder + "unscreenedMean/"      
    #downloadMODIS_All_Years(rawData,"MEAN",unscreenedRasterFolder,START_YEAR,END_YEAR)
    screenedRasterFolder = parentFolder + "screenedMax/"
    unscreenedRasterFolder =parentFolder + "unscreenedMax/"      
    downloadNDVI_All_Years(rawData,"MAX",unscreenedRasterFolder,START_YEAR,END_YEAR)    

#main()


#for i in range(START_YEAR,END_YEAR+1):
#    outputFile = parentFolder + "/uNDVIx" + str(i) + ".tif"
#    if not os.path.exists(outputFile):
#        mergeRasters(parentFolder + "unscreenedMax/" + str(i),i)
screenedRasterFolder = parentFolder + "screenedMax/"
unscreenedRasterFolder =parentFolder + "unscreenedMax/"    
createRasters(unscreenedRasterFolder,screenedRasterFolder)


            
#focalStatisticsAllRasters(parentFolder + "/screenedMax", 1, parentFolder+ "MaxNDVIFocal/x250")
#focalStatisticsAllRasters(parentFolder + "/screenedMax", 2, parentFolder + "MaxNDVIFocal/x500")
#focalStatisticsAllRasters(parentFolder + "/screenedMax", 4, parentFolder+ "MaxNDVIFocal/x1000")


############### end of downloadGreenspace.py ################