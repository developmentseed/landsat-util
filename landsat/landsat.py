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
from optparse import OptionParser, OptionGroup

import settings
from gs_helper import GsHelper
from clipper_helper import Clipper
from metadata_helper import Metadata
from search_helper import Search
from general_helper import georgian_day, year, reformat_date

# FNULL = open(os.devnull, 'w') #recreating /dev/null


def define_options():

    help_text = """
    Landsat-util helps you with searching Landsat8 metadata and downloading the
    images within the search criteria.

    With landsat-util you can also find rows and paths of an area by searching
    a country name or using a custom shapefile and use the result to further
    narrow your search.

    Syntax:
    %prog [OPTIONS]

    Example uses:
    To search and download images or row 003 and path 003 with a data range
    with cloud coverage of maximum 3.0%:
        %prog -s 01/01/2014 -e 06/01/2014 -l 100 -c 3 -i "003,003"
"""

    parser = OptionParser(usage=help_text)

    search = OptionGroup(parser, "Search",
                         "To search Landsat's Metadata use these options:")

    search.add_option("-i", "--rows_paths",
                       help="Include a search array in this format:"
                       "\"path,row,path,row, ... \"",
                       metavar="\"path,row,path,row, ... \"")
    search.add_option("-s", "--start",
                      help="Start Date - Format: MM/DD/YYYY",
                      metavar="01/27/2014")
    search.add_option("-e", "--end",
                      help="End Date - Format: MM/DD/YYYY",
                      metavar="02/27/2014")
    search.add_option("-c", "--cloud",
                      help="Maximum cloud percentage",
                      metavar="1.00")
    search.add_option("-l", "--limit",
                      help="Limit results. Max is 100",
                      default=100,
                      metavar="100")

    parser.add_option_group(search)

    clipper = OptionGroup(parser, "Clipper",
                          "To find rows and paths of a shapefile or a country "
                          "use these options:")

    clipper.add_option("-f", "--shapefile",
                       help="Path to a shapefile for generating the rows and"
                       "path.",
                       metavar="/path/to/my_shapefile.shp")
    clipper.add_option("-o", "--country",
                       help="Enter country NAME or CODE that will designate "
                       "imagery area, for a list of country syntax visit "
                       "(\"https://docs.google.com/spreadsheets/d/1CgC0rrvvT8uF9dgeNMI0CVVqc0z85N-K9cEVnN01aN8/edit?usp=sharing)\"",
                       metavar="Italy")

    parser.add_option_group(clipper)

    metadata = OptionGroup(parser, "Metadata Updater",
                           "Use this option to update Landsat API if you have"
                           "a local copy running")

    metadata.add_option("-u", "--update-metadata",
                        help="Update ElasticSearch Metadata. Requires access"
                        "to an Elastic Search instance",
                        action='store_true',
                        dest='umeta')

    parser.add_option_group(metadata)

    return parser


def main():
    """
    Main function - launches the program
    """
    # Define options
    parser = define_options()

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
        parser.print_help()
        exit('\nYou must specify an argument.')


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
