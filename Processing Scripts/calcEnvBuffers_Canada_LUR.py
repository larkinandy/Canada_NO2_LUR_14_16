
################# runScripts.py ##################
#
# Contains functions for automating several ArcGIS functions during the development of a Land Use Regression model.
# Functions include generating a series of buffers around points in a shapefile, determining polyline length within each unique buffer,
# and determining arverage raster values within the buffer.
#
# Author: Andrew Larkin
# Created for: Perry Hystad, Oregon State University
# Last modified: 12/08/2014
#
# Requirements:
# ArcGIS with spatial extension (tested on ArcGIS v. 10.2)
# ArcGIS comptabile version of python (tested with Python v. 2.7)
# Python integrated development environment is highly recommended but not required
# StatisticsForOverlappingZones.py script (provided by NOAA) is required for the batchRasterBufferIntersect function
# BufferVariables.py contains many custom functions called by runScripts.py
# constantValues.py conatins all modifiable input values (e.g. input files, folder locations)

############## import required modules ###############
import os
import BufferVariables
import multiprocessing
import arcpy
import constantValues as values
import gc
arcpy.env.overwriteOutput = True
import shutil
import time
import constantValues
############## end of module import ##################



########### helper functions ################

# create all of the buffer zones for all of the air monitor partitions 
def makeBufferZones(airMonitorPartitions):
    pool = multiprocessing.Pool()
    pool.map(BufferVariables.makeMultipleBuffers, airMonitorPartitions) # run make buffer zones on parallel processes
    pool.close()
    pool.join()    
    print ("completed making buffer zones for all partitions")
    del pool
### end of makeBufferZones ###

def determineRasterList(airMonitor, rasterValues):
    for fileName in values.RASTER_LIST:
        rasterValues.append(fileName)
    if(len(values.MOSAIC_RASTER_LIST) > 0):
        for variable in values.MOSAIC_RASTER_LIST:
            zone = BufferVariables.determineAirMonitorZone(airMonitor)
            mosaicFilename = BufferVariables.determineMosaicFile(variable,zone,values.RASTER_TYPE)
            # print(mosaicFilename)   
            rasterValues.append(mosaicFilename)        
    # print(rasterValues)

def determinePolylineList(airMonitor, polyLineValues):
    for fileName in values.POLYLINE_LIST:
        polyLineValues.append(fileName)
    if(len(values.POLLYLINE_MOSAIC_LIST) > 0):
        for variable in values.POLLYLINE_MOSAIC_LIST:
            zone = BufferVariables.determineAirMonitorZone(airMonitor)
            mosaicFilename = BufferVariables.determineMosaicFile(variable,zone,values.POLYLINE_TYPE)
            #print(mosaicFilename)
            polyLineValues.append(mosaicFilename) 
    #print(polyLineValues)

def determinePointBufferList(airMonitor, pointBufferList):
    for fileName in values.POINT_BUFFER_LIST:
        pointBufferList.append(fileName)
    

def determinePointList(airMonitor, pointList):
    for file in values.POINT_LIST:
        pointList.append(file)
    if(len(values.POINT_MOSAIC_LIST) > 0):
        for variable in values.POINT_MOSAIC_LIST:
            zone = BufferVariables.determineAirMonitorZone(airMonitor)
            mosaicFilename = BufferVariables.determineMosaicFile(variable,zone,values.POINT_TYPE)
            pointList.append(mosaicFilename)

# setup and calculate average values for a buffer zone
def processBufferVariables(partitionFolderOut, masterBufferFile, identifier, buffer, airMonitor,variableType, fileList):
    readyToJoin = False
    continueVar = True
    while (continueVar):
        try:
            argumentList = []
            argumentList2 = []
            argumentList3 = []
            argVars = []
            if(variableType == values.PARALLEL_PROCESSING):
                rasterList = fileList[0]
                polylineList = fileList[1]  
                if(len(fileList)>0):
                    print("the polylineList is " + str(len(polylineList)))
                    pool = multiprocessing.Pool(len(polylineList))
                    if(len(polylineList) >0):
                        argumentList = []
                        argumentList = BufferVariables.createArgumentList(polylineList, partitionFolderOut, masterBufferFile,identifier,buffer,airMonitor)  
                        #pool = multiprocessing.Pool(len(polylineList))
                        result = pool.map(BufferVariables.multi_run_polyline_wrapper,argumentList2)  # calculate average polyline values on parallel processors
                        pool.close()
                        pool.join()
                        readyToJoin = BufferVariables.testFileCompletion(argumentList)  
                    #BufferVariables.testProgress(result)
                    #readyToJoin = BufferVariables.testFileCompletion(argumentList2)  
            elif(variableType == values.RASTER_TYPE): # if the variable files are from rasters, run the raster wrapper function
                if(len(fileList)>0):
                    pool = multiprocessing.Pool(processes=2)
                    #pool = multiprocessing.Pool(len(fileList))
                    argumentList = BufferVariables.createArgumentList(fileList, partitionFolderOut, masterBufferFile,identifier,buffer,airMonitor)  
                    
                    result = pool.map_async(BufferVariables.multi_run_raster_wrapper,argumentList) # calculate average raster values on parellel processors
                    #time.sleep(60)
                    BufferVariables.testProgress(result)
                    readyToJoin = BufferVariables.testFileCompletion(argumentList)
            elif(variableType == values.POLYLINE_TYPE): # if the variable files are from polyline shp files, ru nthe polyline wrapper function      
                if(len(fileList)>0):
                    pool = multiprocessing.Pool(len(fileList))
                    argumentList2 = BufferVariables.createArgumentList(fileList, partitionFolderOut, masterBufferFile,identifier,buffer,airMonitor)  
                    result = pool.map(BufferVariables.multi_run_polyline_wrapper,argumentList2)  # calculate average polyline values on parallel processors
                    pool.close()
                    pool.join() 
                    readyToJoin=True
            elif(variableType==values.POINT_BUFFER_TYPE):
                if(len(fileList)>0):
                    argumentList3 = BufferVariables.createArgumentList(fileList, partitionFolderOut, masterBufferFile,identifier,buffer,airMonitor)
                    BufferVariables.pointBufferIntersect(argumentList3[0][0], argumentList3[0][1],argumentList3[0][2], argumentList3[0][3], argumentList3[0][4])
                    readyToJoin=True
            if(readyToJoin):
                for argument in argumentList: # for each variable that was used to calculate an average values, add the value to the air monitor partition shp file
                    # print("hot dog") for debugging purposes only
                    BufferVariables.addVariableToPartition(argument, airMonitor,values.RASTER_TYPE)
                for argument in argumentList2:
                    BufferVariables.addVariableToPartition(argument, airMonitor,values.POLYLINE_TYPE)
                for argument in argumentList3:
                    BufferVariables.addVariableToPartition(argument, airMonitor,values.POINT_BUFFER_TYPE)
            else:
                raise Exception
            #print("sucessfully added buffer variables")
        except Exception as e:
            print("couldn't process variables, loop will cycle again" + str(e))
            pool.terminate()
            continue
        finally:
            if(variableType == values.RASTER_TYPE) or(variableType == values.PARALLEL_PROCESSING):
                try:
                    pool.terminate()
                except:
                    print("could not terminate pool")
                try:
                    dirList = os.listdir(values.RESULTS_FOLDER + values.TEMP_STATS_WORKSPACE)
                    for dirFolder in dirList:
                        path = values.RESULTS_FOLDER + values.TEMP_STATS_WORKSPACE + "/" + dirFolder
                        dirList2 = os.listdir(path)
                        for dirFolder2 in dirList2:
                            path2 = path + "/" + dirFolder2
                            dirList3 = os.listdir(path2)
                            for dirFolder3 in dirList3:
                                path3 = path2 + "/" + dirFolder3
                                try:
                                    shutil.rmtree(path3)    
                                except:
                                    #print("couldn't remove filepath " + path3)
                                    exceptTemp = 1
                                try:
                                    fileList = os.listdir(path3)
                                    print(fileList)
                                    for filename in fileList:
                                        try:
                                            os.remove(path2 +"/" + filename)
                                        except:
                                            # print("warning: could not delete the temp stats file " + filename )
                                            exceptTemp = 1
                                except:
                                    excpetTemp = 1 
                                    #print("warning: could not delete the temp stats files")                
                except:
                    # print("couldn't delete the list directories")                               
                    exceptTemp = 1
        break
    print("finished calculating " + str(variableType) + " type values for buffer " + str(buffer) + " of air monitor partition " + identifier)     
    try:
        del pool, argVars, argumentList, fileList
    except:
        print("couldn't delete pool")
    
### end of processBufferVariables       
  
    
########## end of helper functions ###############
 
 
 
 
 
############ main function ##################
def main():
    print("running main")
    if not os.path.exists(values.RESULTS_FOLDER + values.TEMP_STATS_WORKSPACE): os.makedirs(values.RESULTS_FOLDER + values.TEMP_STATS_WORKSPACE)
    #BufferVariables.runPointAnalysis()  # get point values 
    zonesDefined = BufferVariables.assignZones()
    if not os.path.exists(constantValues.RESULTS_FOLDER + constantValues.TEMP_STATS_WORKSPACE): os.makedirs(constantValues.RESULTS_FOLDER + constantValues.TEMP_STATS_WORKSPACE)   
    print("defined buffer zones")
    airMonitorPartitions = BufferVariables.partitionShapefile(zonesDefined) # partition air monitor stations
    print("defined air monitor partitions")
    airMonitorPartitions = airMonitorPartitions[0:len(airMonitorPartitions)]
    makeBufferZones(airMonitorPartitions) # make buffer zones for each partition
    i=0
    for airMonitor in airMonitorPartitions: # for each air monitor partition
        startTime = time.time()
        if(i>=0):
            rasterList = []
            polyLineList = []
            pointList = []
            pointBufferList = []
            determineRasterList(airMonitor,rasterList)
            determinePolylineList(airMonitor, polyLineList)
            determinePointList(airMonitor, pointList)
            determinePointBufferList(airMonitor, pointBufferList)
            print(pointList)
            #BufferVariables.runPointAnalysis(airMonitor, pointList)
            identifier = BufferVariables.determineAirMonitorIdentifier(airMonitor) # determine the partition number
            partitionFolderOut = values.RESULTS_FOLDER + values.KEYWORD + identifier + "/" 
            for buffer in values.BUFFER_DISTANCE: # for each buffer radius          
                bufferFilename = "buffer" + str(buffer) + "m.shp" 
                masterBufferFile = values.RESULTS_FOLDER + values.KEYWORD + identifier + values.BUFFER_EXTENSION + bufferFilename 
                maxThreads = 1 #multiprocessing.cpu_count()*2 -2
                if(1 > 5):#maxThreads >= len(rasterList) + len(polyLineList)):
                    print("running polyline and raster buffer variables in parallel")
                    parallelList = [rasterList,polyLineList]
                    processBufferVariables(partitionFolderOut, masterBufferFile, identifier, buffer, airMonitor, values.PARALLEL_PROCESSING, parallelList)
                    processBufferVariables(partitionFolderOut, masterBufferFile, identifier, buffer, airMonitor, values.POINT_BUFFER_TYPE, pointBufferList)
                else:
                    processBufferVariables(partitionFolderOut, masterBufferFile, identifier, buffer, airMonitor,values.RASTER_TYPE, rasterList) # get average raster values
                    #processBufferVariables(partitionFolderOut, masterBufferFile, identifier, buffer, airMonitor,values.POLYLINE_TYPE,polyLineList) # get average polyline values
                    #processBufferVariables(partitionFolderOut, masterBufferFile, identifier, buffer, airMonitor,values.POINT_BUFFER_TYPE,pointBufferList) # get average point values
                print ("completed buffer distance " + str(buffer) + " for air Monitor partition " + str(identifier))
            #print("completed gathering buffer values for air monitoring station partition " + str(identifier))
            print("time required to process partition " + str(identifier) + ": " + str(time.time()-startTime))
        i+=1
        print("completed gathering buffer values for all air monitoring station partitions")
    arcpy.Merge_management(inputs=airMonitorPartitions,output=values.RESULTS_FOLDER + "final.shp",field_mappings="#")  
    #arcpy.ExportXYv_stats
    print ("completed running the main script")

### end of main function ###
    

# run the main function
if __name__ == '__main__':
    main()
    
    
########## end of runScripts.py ###############