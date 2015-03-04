# Landsat Util
# License: CC0 1.0 Universal

##
# Main Setting File
##

from os import getenv
from os.path import join, expanduser, abspath, dirname

# Google Storage Landsat Config

DEBUG = getenv('DEBUG', False)

SATELLITE = 'L8'
L8_METADATA_URL = 'http://landsat.usgs.gov/metadata_service/bulk_metadata_files/LANDSAT_8.csv'
GOOGLE_STORAGE = 'http://storage.googleapis.com/earthengine-public/landsat/'
S3_LANDSAT = 'http://landsat-pds.s3.amazonaws.com/'
API_URL = 'https://api.developmentseed.org/landsat'

# User's Home Directory
HOME_DIR = expanduser('~')

# Utility's base directory
BASE_DIR = abspath(dirname(__file__))

LANDSAT_DIR = join(HOME_DIR, 'landsat')
DOWNLOAD_DIR = join(LANDSAT_DIR, 'downloads')
PROCESSED_IMAGE = join(LANDSAT_DIR, 'processed')
