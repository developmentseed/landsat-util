#!/usr/bin/env python

# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco, KAPPS-
#
# License: CC0 1.0 Universal

from __future__ import print_function
import sys
import subprocess
import argparse
import textwrap
import json

from dateutil.parser import parse

from gs_helper import GsHelper
from clipper_helper import Clipper
from search_helper import Search
from general_helper import reformat_date
from image_helper import Process
import settings


DESCRIPTION = """Landsat-util is a command line utility that makes it easy to
search, download, and process Landsat imagery.

    Commands:
        Search:
        landsat.py search [-h] [-l LIMIT] [-s START] [-e END] [-c CLOUD]
                     [--onlysearch] [--imageprocess]
                     {pr,shapefile,country}

        positional arguments:
            {pr,shapefile,country}
                                Search commands
            pr                  Activate paths and rows
            shapefile           Activate Shapefile
            country             Activate country

            optional arguments:
            -h, --help            show this help message and exit
            -l LIMIT, --limit LIMIT
                                Search return results limit default is 100

            -s START, --start START
                                Start Date - Most formats are accepted e.g.
                                Jun 12 2014 OR 06/12/2014

            -e END, --end END   End Date - Most formats are accepted e.g.
                                Jun 12 2014 OR 06/12/2014

            -c CLOUD, --cloud CLOUD
                                Maximum cloud percentage default is 20 perct

            -d, --download        Use this flag to download found images

            --imageprocess      If this flag is used, the images are downloaded
                                and process. Be cautious as it might take a
                                long time to both download and process large
                                batches of images

            --pansharpen        Whether to also pansharpen the process image.
                                Pansharpening takes a long time

        Download:
        landsat download [-h] sceneID [sceneID ...]

        positional arguments:
            sceneID     Provide Full sceneID, e.g. LC81660392014196LGN00

        Process:
        landsat.py process [-h] [--pansharpen] path

        positional arguments:
            path          Path to the compressed image file

        optional arguments:
            --pansharpen  Whether to also pansharpen the process image.
                          Pansharpening takes a long time
"""


def args_options():
    parser = argparse.ArgumentParser(prog='landsat',
                        formatter_class=argparse.RawDescriptionHelpFormatter,
                        description=textwrap.dedent(DESCRIPTION))

    subparsers = parser.add_subparsers(help='Landsat Utility',
                                       dest='subs')

    # Search Logic
    parser_search = subparsers.add_parser('search',
                                          help='Search Landsat metdata')

    # Global search options
    parser_search.add_argument('-l', '--limit', default=100, type=int,
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
    parser_search.add_argument('-d', '--download', action='store_true',
                               help='Use this flag to download found images')
    parser_search.add_argument('--imageprocess', action='store_true',
                               help='If this flag is used, the images are '
                               'downloaded and process. Be cautious as it '
                               'might take a long time to both download and '
                               'process large batches of images')
    parser_search.add_argument('--pansharpen', action='store_true',
                               help='Whether to also pansharpen the process '
                               'image. Pan sharpening takes a long time')

    search_subparsers = parser_search.add_subparsers(help='Search commands',
                                                     dest='search_subs')

    search_pr = search_subparsers.add_parser('pr',
                                             help="Activate paths and rows")
    search_pr.add_argument('paths_rows',
                           metavar='path_row',
                           type=int,
                           nargs="+",
                           help="Provide paths and rows")

    search_shapefile = search_subparsers.add_parser('shapefile',
                                                    help="Activate Shapefile")
    search_shapefile.add_argument('path',
                                  help="Path to shapefile")

    search_country = search_subparsers.add_parser('country',
                                                  help="Activate country")
    search_country.add_argument('name', help="Country name e.g. ARE")

    parser_download = subparsers.add_parser('download',
                                            help='Download images from Google Storage')
    parser_download.add_argument('scenes',
                                 metavar='sceneID',
                                 nargs="+",
                                 help="Provide Full sceneID, e.g. "
                                 "LC81660392014196LGN00")

    parser_process = subparsers.add_parser('process',
                                           help='Process Landsat imagery')
    parser_process.add_argument('path',
                                help='Path to the compressed image file')
    parser_process.add_argument('--pansharpen', action='store_true',
                                help='Whether to also pansharpen the process '
                                'image. Pan sharpening takes a long time')

    return parser


def main(args):
    """
    Main function - launches the program
    """

    if args:
        if args.subs == 'process':
            p = Process(args.path)
            if args.pansharpen:
                p.full_with_pansharpening()
            else:
                p.full()

            exit("The output is stored at %s." % settings.PROCESSED_IMAGE)

        elif args.subs == 'search':

            try:
                if args.start:
                    args.start = reformat_date(parse(args.start))

                if args.end:
                    args.end = reformat_date(parse(args.end))
            except TypeError:
                exit("You date format is incorrect. Please try again!", 1)

            s = Search()
            if args.search_subs == 'pr':
                result = s.search(row_paths=args.paths_rows,
                                  limit=args.limit,
                                  start_date=args.start,
                                  end_date=args.end,
                                  cloud_max=args.cloud)

            elif args.search_subs == 'shapefile':
                clipper = Clipper()
                result = s.search(clipper.shapefile(args.path),
                                  limit=args.limit,
                                  start_date=args.start,
                                  end_date=args.end,
                                  cloud_max=args.cloud)
            elif args.search_subs == 'country':
                clipper = Clipper()
                prs = clipper.country(args.name)
                if prs:
                    result = s.search(prs,
                                      limit=args.limit,
                                      start_date=args.start,
                                      end_date=args.end,
                                      cloud_max=args.cloud)
            try:
                if result['status'] == 'SUCCESS':
                    print('%s items were found' % result['total'])
                    if result['total'] > 100:
                        exit('Too many results. Please narrow your search')
                    else:
                        print(json.dumps(result, sort_keys=True, indent=4))
                    # If only search
                    if args.download:
                        gs = GsHelper()
                        print('Starting the download:')
                        for item in result['results']:
                            gs.single_download(row=item['row'],
                                               path=item['path'],
                                               name=item['sceneID'])
                        print("%s images were downloaded"
                              % result['total_returned'])
                        if args.imageprocess:
                            for item in result['results']:
                                p = Process('%s/%s.tar.bz' % (gs.zip_dir,
                                                              item['sceneID']))
                                if args.pansharpen:
                                    p.full_with_pansharpening()
                                else:
                                    p.full()
                        else:
                            exit("The downloaded images are located here: %s" %
                                 gs.zip_dir)
                    else:
                        exit('Done!')
                elif result['status'] == 'error':
                    exit(result['message'])
            except KeyError:
                exit('Too Many API queries. You can only query DevSeed\'s '
                     'API 5 times per minute', 1)
        elif args.subs == 'download':
            gs = GsHelper()
            print('Starting the download:')
            for scene in args.scenes:
                gs.single_download(row=gs.extract_row_path(scene)[1],
                                   path=gs.extract_row_path(scene)[0],
                                   name=scene)
            exit("The downloaded images are located here: %s" % gs.zip_dir)


def exit(message, code=0):
    print(message)
    sys.exit(code)


def package_installed(package):
    """
    Check if a package is installed on the machine
    """

    print("Checking if %s is installed on the system" % package)
    installed = not subprocess.call(["which", package])
    if installed:
        print("%s is installed" % package)
        return True
    else:
        print("You have to install %s first!" % package)
        return False


def __main__():

    global parser
    parser = args_options()
    args = parser.parse_args()
    main(args)

if __name__ == "__main__":
    __main__()
