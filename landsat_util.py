#!/usr/bin/env python

# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco
#
# License: CC0 1.0 Universal

import sys
import subprocess
import datetime
from optparse import OptionParser

import landsat_util.settings
from landsat_util.gs_helper import GsHelper
from landsat_util.clipper_helper import Clipper
from landsat_util.metadata_helper import Metadata

# FNULL = open(os.devnull, 'w') #recreating /dev/null


def main():
    """
    Main function - launches the program
    """
    # Define options
    parser = OptionParser()
    parser.add_option("--search_array",
                      help="Include a search array in this format: \
                      \"path,row,path,row, ... \"",
                      metavar="\"path,row,path,row, ... \"")
    parser.add_option("--start",
                      help="Start Date - Format: MM/DD/YYYY",
                      metavar="01/27/2014")
    parser.add_option("--end",
                      help="End Date - Format: MM/DD/YYYY",
                      metavar="02/27/2014")
    parser.add_option("--shapefile",
                      help="Generate rows and paths from a shapefile. You must\
                       create a folder called 'shapefile_input'. You must add \
                       your shapefile to this folder.",
                      metavar="my_shapefile.shp")
    parser.add_option("--country",
                      help="Enter country NAME or CODE that will designate \
                      imagery area, for a list of country syntax visit \
                      (\"https://docs.google.com/spreadsheets/d/1CgC0rrvvT8uF9dgeNMI0CVVqc0z85N-K9cEVnN01aN8/edit?usp=sharing)\"",
                      metavar="Italy")
    parser.add_option("--update-metadata",
                      help="Update ElasticSearch Metadata. Requires access \
                      to an Elastic Search instance",
                      action='store_true',
                      dest='umeta')

    (options, args) = parser.parse_args()

    # Raise an error if no option is given
    raise_error = True

    # Execute search_array sequence
    if options.search_array:
        raise_error = False
        array = search_array_check(options.search_array)

        if options.start and options.end:
            fmt = '%m/%d/%Y'
            date_rng = {
                'start_y': datetime.datetime
                                   .strptime(options.start, fmt)
                                   .timetuple()
                                   .tm_year,
                'start_jd': datetime.datetime
                                    .strptime(options.start, fmt)
                                    .timetuple().tm_yday,
                'end_y': datetime.datetime
                                 .strptime(options.end, fmt)
                                 .timetuple().tm_year,
                'end_jd': datetime.datetime
                                  .strptime(options.end, fmt)
                                  .timetuple().tm_yday
            }

        gs = GsHelper(landsat_util.settings)
        gs.download(gs.search(array, date_rng))

        if gs.found > 0:
            gs.unzip()
            print "%s images were downloaded and unzipped!" % gs.found
            exit("Your unzipped images are located here: %s" % gs.unzip_dir)
        else:
            exit("No Images found. Change your search parameters.")

    if options.shapefile:
        raise_error = False
        clipper = Clipper()
        clipper.shapefile(options.shapefile)
        exit("Shapefile clipped")

    if options.country:
        raise_error = False
        clipper = Clipper()
        clipper.country(options.country)
        exit("Process Completed")

    if options.umeta:
        raise_error = False
        meta = Metadata()
        print 'Starting Metadata Update using Elastic Search ...\n'
        meta.populate()

    if raise_error:
        exit('You must specify an argument. Use landsat_util --help for ' +
             'more info')


def exit(message):
    print message
    sys.exit()


def search_array_check(search_array):
    """
    Turn the search text into paired groups of two
    """
    array = search_array.split(',')
    paired = []
    for i in xrange(0, len(array), 2):
        paired.append(array[i:i + 2])

    return paired


def package_installed(package):
    """
    Check if a package is installed on the machine
    """

    print "Checking if %s is installed on the system" % package
    installed = not subprocess.call(["which", package])
    if installed:
        print "%s is installed" % package
        return True
    else:
        print "You have to install %s first!" % package
        return False


if __name__ == "__main__":
    main()
