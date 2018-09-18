############## define settings and variables #########
KEYWORD = "Partition"
ZONE_KEYWORD = 'z'
PARTITION_KEYWORD = "i"
RASTER_TYPE = 0
POLYLINE_TYPE = 1
POINT_TYPE = 3
PARALLEL_PROCESSING = 2
POINT_BUFFER_TYPE = 4
BUFFER_EXTENSION = "/buffers/"
AIRMONITOR_ID = "FID"
TABLE_ID = "ORIG_FID"
BUFFER_ID = "FID_buffer"
LENGTH_COMMAND = "!shape.length@kilometers!" # command for field calculator operation
CARBON_COMMAND = "!SUM_carbon! * 1"
TEMP_STATS_WORKSPACE = "tempStats"
RATER_PROCESS_WAIT_TIME = 60
TEST_PROGRESS_FILE = "test_progress.txt"

PARENT_FOLDER = "C:/users/larkinan/desktop/CanadaLUR/"#"S:/Restricted/PURE_AIR/Canada_LUR_NO2/"
INPUT_FOLDER = PARENT_FOLDER + "screenedMax/"
MONITOR_FILE= "AirMonitors_Screened_Albers.shp"
RESULTS_FOLDER = PARENT_FOLDER + "Results/"

#MONITOR_FILE = "zone5.shp"
#INPUT_FOLDER ="C:/users/larkinan/desktop/Global_LUR_processing/pyInput/"
#RESULTS_FOLDER = "C:/users/larkinan/desktop/Global_LUR_processing/pyResults/"
MOSAIC_RASTER_LIST = []
POLLYLINE_MOSAIC_LIST = []

#POLYLINE_LIST = ["RailAndTransitLine_Albers.shp",
#                "aRDS_C123_Albers.shp", 
#                "bRDS_expressways_Albers.shp",
#                "cRDS_highways_Albers.shp",
#                "dRDS_Local_Albers.shp",
#                "eRDS_Major_Albers.shp",
#                "fRDS_Truck_Restrictions_Albers.shp"]


#POLYLINE_LIST = ["aLU_Industriall_Albsers_Dissolve.shp",
#                 "bLU_Open_Parksl_Albsers_Dissolve.shp",
#                 "cLU_Residential_Albsers_Dissolve.shp"]
POLYLINE_LIST = []


                         
POINT_BUFFER_LIST = []
POINT_MOSAIC_LIST = []
POINT_LIST = [] #TODO include NO2 satellite raster?
RASTER_LIST = ["N6.tif","water_body5.tif"]

ZONE_DEFINITIONS = "zoneDef.shp"
#POLYLINE_LIST = []
#COAST_BOUNDARY = "coastline.shp"
#BUFFER_DISTANCE =[2000,200]
BUFFER_DISTANCE = [50,100,250,500,750,1000,2000,3000,4000,5000,10000,15000,20000]
#BUFFER_DISTANCE = [100,1000,10000]
PARTITION_SIZE = 50

####### end of define settings and variables #########