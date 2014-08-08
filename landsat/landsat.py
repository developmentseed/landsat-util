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

import settings
from gs_helper import GsHelper
from clipper_helper import Clipper
from metadata_helper import Metadata
from search_helper import Search
from general_helper import georgian_day, year, reformat_date

# FNULL = open(os.devnull, 'w') #recreating /dev/null


def define_options(parser):
    parser.add_option("-m",
                      help="Use Metadata API to search",
                      action='store_true',
                      dest='use_metadata')
    parser.add_option("--rows_paths",
                      help="Include a search array in this format: \
                      \"path,row,path,row, ... \"",
                      metavar="\"path,row,path,row, ... \"")
    parser.add_option("--start",
                      help="Start Date - Format: MM/DD/YYYY",
                      metavar="01/27/2014")
    parser.add_option("--end",
                      help="End Date - Format: MM/DD/YYYY",
                      metavar="02/27/2014")
    parser.add_option("--cloud",
                      help="Maximum cloud percentage",
                      metavar="1.00")
    parser.add_option("--limit",
                      help="Limit results. Max is 100",
                      default=100,
                      metavar="100")
    parser.add_option("--shapefile",
                      help="Generate rows and paths from a shapefile. You " +
                      "must create a folder called 'shapefile_input'. You " +
                      "must add your shapefile to this folder.",
                      metavar="my_shapefile.shp")
    parser.add_option("--country",
                      help="Enter country NAME or CODE that will designate " +
                      "imagery area, for a list of country syntax visit " +
                      "(\"https://docs.google.com/spreadsheets/d/1CgC0rrvvT" +
                      "8uF9dgeNMI0CVVqc0z85N-K9cEVnN01aN8/edit?usp=sharing)\"",
                      metavar="Italy")
    parser.add_option("--update-metadata",
                      help="Update ElasticSearch Metadata. Requires access \
                      to an Elastic Search instance",
                      action='store_true',
                      dest='umeta')
    return parser


def main():
    """
    Main function - launches the program
    """
    # Define options
    parser = OptionParser()
    parser = define_options(parser)

    (options, args) = parser.parse_args()

    # Raise an error if no option is given
    raise_error = True

    # Execute rows_paths sequence
    if options.rows_paths:
        raise_error = False
        array = rows_paths_check(options.rows_paths)
        date_rng = None
        gs = GsHelper(settings)

        if options.use_metadata:
            s = Search()
            result = s.search(row_paths=options.rows_paths,
                              start_date=reformat_date(options.start,
                                                       '%Y-%m-%d'),
                              end_date=reformat_date(options.end,
                                                     '%Y-%m-%d'),
                              cloud_max=options.cloud,
                              limit=100)

            if result['status'] == 'SUCCESS':
                print '%s items were found' % result['total_returned']
                print 'Starting the download:'
                for item in result['results']:
                    gs.download_single(row=item['row'],
                                       path=item['path'],
                                       name=item['sceneID'])
                    gs.unzip()
                    print "%s images were downloaded and unzipped!" % result['total_returned']
                    exit("Your unzipped images are located here: %s" %
                         gs.unzip_dir)
            elif result['status'] == 'error':
                exit(result['message'])

        else:
            date_rng = {
                'start_y': year(options.start),
                'start_jd': georgian_day(options.start),
                'end_y': year(options.end),
                'end_jd': georgian_day(options.end)
            }

            gs.download(gs.search(array, date_rng))

            if gs.found > 0:
                gs.unzip()
                print "%s images were downloaded and unzipped!" % gs.found
                exit("Your unzipped images are located here: %s" %
                     gs.unzip_dir)
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


def rows_paths_check(rows_paths):
    """
    Turn the search text into paired groups of two
    """
    array = rows_paths.split(',')
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
