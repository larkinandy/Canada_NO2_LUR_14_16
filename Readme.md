# Documentation for the 2014-2016 Canada NO2 LUR Model #

**Author:** [Andrew Larkin](https://www.linkedin.com/in/andrew-larkin-525ba3b5/) <br>
**Affiliation:** [Oregon State University, College of Public Health and Human Sciences](https://health.oregonstate.edu/) <br>
**Principal Investigator:** [Perry Hystad](https://health.oregonstate.edu/people/perry-hystad) <br>
**Date Created:** September 14th, 2018

### Summary ###
This notebook contains the codebook, datasources, and names of R and python scripts used to develop the 2014-2016 three year average LUR NO2 model for Canada.  The sections of the notebook are as follows: <br> <br>
**1 Codebook:** names and characteristics of variables used in the LUR model <br>
**2 Datasources:** underlying sources of data used to derive the variables in the codebook <br>
**3 Processing scripts:** names and descriptons of the scripts used to derie variables in the codebook and develop the land use regresson model <br>

### Codebook ####

Variables in the codebook are partitioned into distance-based, point-based, and buffer-based variables. All buffer distances are in meters<br>

#### Distance based variables #### 
- **port_dist** - distance to nearest port. Units: meters. Datatype: Float. Datasource: 5.

#### Point based variables ####

- **elevation** - air monitor elevation level. Units: meters. Datatype: Int. Datasource: 7.
- **mean_20YY** - annual mean NO2 concentration. Units: ppb. Datatype: Int.  Datasource: 7.
- **meanNO2_2014_2016** - average of annual mean NO2 concentrations from 2014 to 2016. Units: ppb. Datatype: Float. Datasource: 7.
- **NAPS ID** - air monitor station id. Datatype: Int. Datasource: 7.
- **numObs** - number of annual mean NO2 concentration measures between 2014 and 2016. Datatype: Int.  Datasource: 7.
- **percent completeness_20YY** - percent air monitor coverage for year YY. Datatype: Int. Datasource: 7.
- **pr_YY** - annual mean daily precipitation for year YY. Units: nm. Datatpye: Float. Datasource: 1.
- **pr_14_16** - mean of pr_14, pr_15, and pr_16. Units: nm. Datatype: Float. Datasource: 1.
- **te_YY** - annual mean daily max temperature for year YY. Units: degrees celcius. Datatype: Float. Datasource: 1.
- **te_14_16** - mean of te_14, te_15, and te_16. Units: degrees celcius. Datatype: Float. Datasource: 1.
- **sat_10_12** - annual mean NO2. Units: ppb. Datatype: Float. Datasource: 2.

#### Buffer based variables #### 

buffer distances range from 10m to 20km.  Units are in meters and the datatype is float for buffer based variables unless indicated otherwise
- **alXXXXm** - sum area of industrial land use in buffer distance XXXX. Datasource: 5.
- **blXXXXm** - sum area of open space or parks in buffer distance XXXX. Datasource: 5.
- **bRXXXXm** - length of expressways in buffer distance XXXX. Datasource: 5.
- **clXXXXm** - sum area of residential land use in buffer distance XXXX. Datasource 5.
- **cRXXXXm** - length of highways in buffer distance XXXX. Datasource: 5. 
- **dRXXXXm** - length of local roads in buffer distance XXXX. Datasource: 5.
- **eRXXXXm** - length of major roads in buffer distance XXXX. Datasource: 5.
- **fRXXXXm** - length of roads with truck restrictions in buffer distance XXXX. Datasource: 5.
- **RaXXXXm** - length of railway and transit lines in buffer distance XXXX. Datasource: 5.
- **waXXXXm** - percent area water in buffer distance XXXX.  Datasource 3.
- **NDVI_14_16_XXXXm** - three year (2014-2016) average of mean value of max annual NDVI in buffer distance XXXX. Datasource: 4.
- **NYXXXXm** - mean value of max annual NDVI in buffer distance XXXX for year 201Y. Datasource 4.



### Datasources ###

1. **Daymet V3: Daily Surface Weather and Climatological Summaries**  Author: NASA.  Spatial Resolution: 1000m. Temporal Resolution: Daily. Downloaded from the Google Earth Engine (https://explorer.earthengine.google.com/#detail/NASA%2FORNL%2FDAYMET_V3) <br>
2. **Geddes, J. A.; Martin, R. V.; Boys, B. L.; van Donkelaar, A. Long-term trends worldwide in ambient NO2 concentrations inferred from satellite observations. Environ. Health Perspect. Online 2016, 124 (3), 281** Spatial Resolution: 1km.  Temporal Resolution: three year rolling average.  <br> 
3. **GLCF: Landsat Global Inland Water.** Author: GCLF.  Spatial Resolution: 30m.  Temporal Resolution: Basd on year 2000.  Downloaded from Google Earth Engine (https://developers.google.com/earth-engine/datasets/catalog/GLCF_GLS_WATER)
4. **Landsat 8 Collection 1 Tier 1 8-Day NDVI Composite. ** Author: Google.  Spatial Resolution: 30m.  Temporal Resolution: 8day.  Downloaded from Google Earth Engine (https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C01_T1_8DAY_NDVI).  
5. **Canda Geospatial Data.** Author: DTMI. Spatial Resolution: NA.  Temporal Resolution: Annual, 2015.
6. **Population Density.** Author: Statistics Canada.  Spatial Resolution: Census Block.  Temporal Resolution: Based on year 2016.
7. **National Air Pollutants Surveillance Program NO2 Measurements** Author: Department of the Environment, Canada.  Spatial Resolution: NA.  Temporal Resolution: Annual.
8. **National Pollutant Release Inventory** Author: Department of the Environment, Canada. Spatial Resolution: NA. Temporal Resolution: Annual, based on year 2016. 

### Processing Scripts ###

Scripts 1 through 4 were used to derived exposure estimates.  Script 5 was used to preprocess data, and script 6 was used to create the LUR model.

1. [**downloadEnvRasters_Canada_LUR.py**](https://github.com/larkinandy/Canada_NO2_LUR_14_16/blob/master/Processing%20Scripts/downloadEnvRasters_Canada_LUR.py) - download NDVI, precipitation, and temperature from Google Earth Engine.  
2. [**calcEnvBuffers_Canada_LUR.py**](https://github.com/larkinandy/Canada_NO2_LUR_14_16/blob/master/Processing%20Scripts/calcEnvBuffers_Canada_LUR.py) - calculate buffer variables for Air Monitor Station Locations.  
3. [**bufferFunctions_Canada_LUR.py**](https://github.com/larkinandy/Canada_NO2_LUR_14_16/blob/master/Processing%20Scripts/bufferFunctions_Canada_LUR.py) - helper functions for script 2.
4. [**constantValues_Canada_LUR.py**](https://github.com/larkinandy/Canada_NO2_LUR_14_16/blob/master/Processing%20Scripts/constantValues_Canada_LUR.py) - constant values for script 2.
5. [**threeYearAverages_Canada_LUR.py**](https://github.com/larkinandy/Canada_NO2_LUR_14_16/blob/master/Processing%20Scripts/threeYearAverages_Canada_LUR.ipynb) - calculate three year averages for NDVI and air monitor NO2 datasets. Merge land use and air monitor datasets.
6. [**sumRoadBuffers_Canada_LUR.ipynb**](https://github.com/larkinandy/Canada_NO2_LUR_14_16/blob/master/Processing%20Scripts/sumRoadBuffers_Canada_LUR.ipynb) - sum road buffer variables to create combinatory road variables (e.g. highways and expressways).
6. [**modelSelection_Canada_LUR.R**](https://github.com/larkinandy/Canada_NO2_LUR_14_16/blob/master/Processing%20Scripts/modelSelection_Canada_LUR.R) - select env variables and create LUR NO2 model.
