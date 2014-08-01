# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco
#
# License: CC0 1.0 Universal

##
## Main Setting File
##

import os

# Google Storage Landsat Config

SOURCE_URL = 'gs://earthengine-public/landsat'
SCENE_FILE_URL = SOURCE_URL + '/scene_list.zip'
SATELLITE = 'L8'
L8_METADATA_URL = 'http://landsat.usgs.gov/metadata_service/bulk_metadata_files/LANDSAT_8.csv'

# Elastic Search Config

ES_URL = 'http://localhost:9200'
ES_MAIN_INDEX = 'landsat'
ES_MAIN_TYPE = '8'

# Local Forlders Config

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DOWNLOAD_DIR = BASE_DIR + '/output/imagery'
ZIP_DIR = DOWNLOAD_DIR + '/zip'
UNZIP_DIR = DOWNLOAD_DIR + '/unzip'
SCENE_FILE = DOWNLOAD_DIR + '/scene_list'

ASSESTS_DIR = BASE_DIR + '/assests'

SHAPEFILE_INPUT = BASE_DIR + '/output/shapefiles/input'
SHAPEFILE_OUTPUT = BASE_DIR + '/output/shapefiles/output'
