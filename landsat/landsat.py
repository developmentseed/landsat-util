#!/usr/bin/env python

# Landsat Util
# License: CC0 1.0 Universal

import argparse
import textwrap
import json

from dateutil.parser import parse
import pycurl

from downloader import Downloader, IncorrectSceneId
from search import Search
from utils import reformat_date, convert_to_integer_list, timer, exit
from mixins import VerbosityMixin
from image import Process, FileDoesNotExist
from __init__ import __version__


DESCRIPTION = """Landsat-util is a command line utility that makes it easy to
search, download, and process Landsat imagery.

    Commands:
        Search:
            landsat.py search [-p --pathrow] [--lat] [--lon] [-l LIMIT] [-s START] [-e END] [-c CLOUD] [-h]

            optional arguments:
                -p, --pathrow       Paths and Rows in order separated by comma. Use quotes "001,003".
                                    Example: path,row,path,row 001,001,190,204

                --lat               Latitude

                --lon               Longitude

                -l LIMIT, --limit LIMIT
                                    Search return results limit default is 10

                -s START, --start START
                                    Start Date - Most formats are accepted e.g.
                                    Jun 12 2014 OR 06/12/2014

                -e END, --end END   End Date - Most formats are accepted e.g.
                                    Jun 12 2014 OR 06/12/2014

                -c CLOUD, --cloud CLOUD
                                    Maximum cloud percentage. Default: 20 perct

                -h, --help          Show this help message and exit

        Download:
            landsat download sceneID [sceneID ...] [-h] [-b --bands]

            positional arguments:
                sceneID     Provide Full sceneIDs. You can add as many sceneIDs as you wish

                Example: landast download LC81660392014196LGN00

            optional arguments:
                -b --bands          If you specify bands, landsat-util will try to download the band from S3.
                                    If the band does not exist, an error is returned

                -h, --help          Show this help message and exit

                -d, --dest          Destination path

        Process:
            landsat.py process path [-h] [-b --bands] [-p --pansharpen]

            positional arguments:
                path          Path to the landsat image folder or zip file

            optional arguments:
                -b --bands             Specify bands. The bands should be written in sequence with no spaces
                                    Default: Natural colors (432)
                                    Example --bands 432

                -p --pansharpen     Whether to also pansharpen the process image.
                                    Pansharpening takes a long time

                -v, --verbose       Show verbose output

                -h, --help          Show this help message and exit
"""


def args_options():
    parser = argparse.ArgumentParser(prog='landsat',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent(DESCRIPTION))

    subparsers = parser.add_subparsers(help='Landsat Utility',
                                       dest='subs')

    parser.add_argument('--version', action='version', version='%(prog)s version ' + __version__)

    # Search Logic
    parser_search = subparsers.add_parser('search',
                                          help='Search Landsat metdata')

    # Global search options
    parser_search.add_argument('-l', '--limit', default=10, type=int,
                               help='Search return results limit\n'
                               'default is 100')
    parser_search.add_argument('-s', '--start',
                               help='Start Date - Most formats are accepted '
                               'e.g. Jun 12 2014 OR 06/12/2014')
    parser_search.add_argument('-e', '--end',
                               help='End Date - Most formats are accepted '
                               'e.g. Jun 12 2014 OR 06/12/2014')
    parser_search.add_argument('-c', '--cloud', type=float, default=20.0,
                               help='Maximum cloud percentage '
                               'default is 20 perct')
    parser_search.add_argument('-p', '--pathrow',
                               help='Paths and Rows in order separated by comma. Use quotes ("001").'
                               'Example: path,row,path,row 001,001,190,204')
    parser_search.add_argument('--lat', type=float, help='The latitude')
    parser_search.add_argument('--lon', type=float, help='The longitude')

    parser_download = subparsers.add_parser('download',
                                            help='Download images from Google Storage')
    parser_download.add_argument('scenes',
                                 metavar='sceneID',
                                 nargs="+",
                                 help="Provide Full sceneID, e.g. LC81660392014196LGN00")

    parser_download.add_argument('-b', '--bands', help='If you specify bands, landsat-util will try to download '
                                 'the band from S3. If the band does not exist, an error is returned')
    parser_download.add_argument('-d', '--dest', help='Destination path')

    parser_process = subparsers.add_parser('process',
                                           help='Process Landsat imagery')
    parser_process.add_argument('path',
                                help='Path to the compressed image file')
    parser_process.add_argument('--pansharpen', action='store_true',
                                help='Whether to also pansharpen the process '
                                'image. Pan sharpening takes a long time')
    parser_process.add_argument('-b', '--bands', help='specify band combinations. Default is 432'
                                'Example: --bands 321')
    parser_process.add_argument('-v', '--verbose', action='store_true',
                                help='Turn on verbosity')

    return parser


def main(args):
    """
    Main function - launches the program
    """

    v = VerbosityMixin()

    if args:
        if args.subs == 'process':
            verbose = True if args.verbose else False
            try:
                bands = convert_to_integer_list(args.bands)
                p = Process(args.path, bands=bands, verbose=verbose)
            except IOError:
                exit("Zip file corrupted", 1)
            except FileDoesNotExist as e:
                exit(e.message, 1)

            stored = p.run(args.pansharpen)

            exit("The output is stored at %s" % stored)

        elif args.subs == 'search':

            try:
                if args.start:
                    args.start = reformat_date(parse(args.start))
                if args.end:
                    args.end = reformat_date(parse(args.end))
            except (TypeError, ValueError):
                exit("You date format is incorrect. Please try again!", 1)

            s = Search()

            try:
                lat = float(args.lat) if args.lat else None
                lon = float(args.lon) if args.lon else None
            except ValueError:
                exit("The latitude and longitude values must be valid numbers", 1)

            result = s.search(paths_rows=args.pathrow,
                              lat=lat,
                              lon=lon,
                              limit=args.limit,
                              start_date=args.start,
                              end_date=args.end,
                              cloud_max=args.cloud)

            if result['status'] == 'SUCCESS':
                v.output('%s items were found' % result['total'], normal=True, arrow=True)
                if result['total'] > 100:
                    exit('Over 100 results. Please narrow your search', 1)
                else:
                    v.output(json.dumps(result, sort_keys=True, indent=4), normal=True, color='green')
                    exit('Search completed!')
            elif result['status'] == 'error':
                exit(result['message'], 1)
        elif args.subs == 'download':
            d = Downloader(download_dir=args.dest)
            try:
                if d.download(args.scenes, convert_to_integer_list(args.bands)):
                    exit('Download Completed', 0)
            except IncorrectSceneId:
                exit('The SceneID provided was incorrect', 1)


def __main__():

    global parser
    parser = args_options()
    args = parser.parse_args()
    with timer():
        main(args)

if __name__ == "__main__":
    try:
        __main__()
    except (KeyboardInterrupt, pycurl.error):
        exit('Received Ctrl + C... Exiting! Bye.', 1)
