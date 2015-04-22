#!/usr/bin/env python

# Landsat Util
# License: CC0 1.0 Universal

import argparse
import textwrap
import json
from os.path import join
from urllib2 import URLError

from dateutil.parser import parse
import pycurl
from boto.exception import NoAuthHandlerFound

from downloader import Downloader, IncorrectSceneId
from search import Search
from uploader import Uploader
from utils import reformat_date, convert_to_integer_list, timer, exit, get_file
from mixins import VerbosityMixin
from image import Process, FileDoesNotExist
from __init__ import __version__
import settings


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

                -p, --process       Process the image after download

                --pansharpen        Whether to also pansharpen the processed image.
                                    Pansharpening requires larger memory

                -u --upload         Upload to S3 after the image processing completed

                --key               Amazon S3 Access Key (You can also be set AWS_ACCESS_KEY_ID as
                                    Environment Variables)

                --secret            Amazon S3 Secret Key (You can also be set AWS_SECRET_ACCESS_KEY as
                                    Environment Variables)

                --bucket            Bucket name (required if uploading to s3)

                --region            URL to S3 region e.g. s3-us-west-2.amazonaws.com

        Process:
            landsat.py process path [-h] [-b --bands] [-p --pansharpen]

            positional arguments:
                path          Path to the landsat image folder or zip file

            optional arguments:
                -b --bands             Specify bands. The bands should be written in sequence with no spaces
                                    Default: Natural colors (432)
                                    Example --bands 432

                --pansharpen        Whether to also pansharpen the process image.
                                    Pansharpening requires larger memory

                -v, --verbose       Show verbose output

                -h, --help          Show this help message and exit

                -u --upload         Upload to S3 after the image processing completed

                --key               Amazon S3 Access Key (You can also be set AWS_ACCESS_KEY_ID as
                                    Environment Variables)

                --secret            Amazon S3 Secret Key (You can also be set AWS_SECRET_ACCESS_KEY as
                                    Environment Variables)

                --bucket            Bucket name (required if uploading to s3)

                --region            URL to S3 region e.g. s3-us-west-2.amazonaws.com
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
    parser_download.add_argument('-p', '--process', help='Process the image after download', action='store_true')
    parser_download.add_argument('--pansharpen', action='store_true',
                                 help='Whether to also pansharpen the process '
                                 'image. Pansharpening requires larger memory')
    parser_download.add_argument('-u', '--upload', action='store_true',
                                 help='Upload to S3 after the image processing completed')
    parser_download.add_argument('--key', help='Amazon S3 Access Key (You can also be set AWS_ACCESS_KEY_ID as '
                                 'Environment Variables)')
    parser_download.add_argument('--secret', help='Amazon S3 Secret Key (You can also be set AWS_SECRET_ACCESS_KEY '
                                 'as Environment Variables)')
    parser_download.add_argument('--bucket', help='Bucket name (required if uploading to s3)')
    parser_download.add_argument('--region', help='URL to S3 region e.g. s3-us-west-2.amazonaws.com')

    parser_process = subparsers.add_parser('process', help='Process Landsat imagery')
    parser_process.add_argument('path',
                                help='Path to the compressed image file')
    parser_process.add_argument('--pansharpen', action='store_true',
                                help='Whether to also pansharpen the process '
                                'image. Pansharpening requires larger memory')
    parser_process.add_argument('-b', '--bands', help='specify band combinations. Default is 432'
                                'Example: --bands 321')
    parser_process.add_argument('-v', '--verbose', action='store_true',
                                help='Turn on verbosity')
    parser_process.add_argument('-u', '--upload', action='store_true',
                                help='Upload to S3 after the image processing completed')
    parser_process.add_argument('--key', help='Amazon S3 Access Key (You can also be set AWS_ACCESS_KEY_ID as '
                                'Environment Variables)')
    parser_process.add_argument('--secret', help='Amazon S3 Secret Key (You can also be set AWS_SECRET_ACCESS_KEY '
                                'as Environment Variables)')
    parser_process.add_argument('--bucket', help='Bucket name (required if uploading to s3)')
    parser_process.add_argument('--region', help='URL to S3 region e.g. s3-us-west-2.amazonaws.com')

    return parser


def main(args):
    """
    Main function - launches the program
    """

    v = VerbosityMixin()

    if args:
        if args.subs == 'process':
            verbose = True if args.verbose else False
            stored = process_image(args.path, args.bands, verbose, args.pansharpen)

            if args.upload:
                u = Uploader(args.key, args.secret, args.region)
                u.run(args.bucket, get_file(stored), stored)

            return ["The output is stored at %s" % stored]

        elif args.subs == 'search':

            try:
                if args.start:
                    args.start = reformat_date(parse(args.start))
                if args.end:
                    args.end = reformat_date(parse(args.end))
            except (TypeError, ValueError):
                return ["You date format is incorrect. Please try again!", 1]

            s = Search()

            try:
                lat = float(args.lat) if args.lat else None
                lon = float(args.lon) if args.lon else None
            except ValueError:
                return ["The latitude and longitude values must be valid numbers", 1]

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
                    return ['Over 100 results. Please narrow your search', 1]
                else:
                    v.output(json.dumps(result, sort_keys=True, indent=4), normal=True, color='green')
                    return ['Search completed!']
            elif result['status'] == 'error':
                return [result['message'], 1]
        elif args.subs == 'download':
            d = Downloader(download_dir=args.dest)
            try:
                if d.download(args.scenes, convert_to_integer_list(args.bands)):
                    if args.process:
                        if args.dest:
                            path = join(args.dest, args.scenes[0])
                        else:
                            path = join(settings.DOWNLOAD_DIR, args.scenes[0])

                        # Keep using Google if the image is before 2015
                        if (int(args.scenes[0][12]) < 5 or not args.bands):
                            path = path + '.tar.bz'

                        stored = process_image(path, args.bands, False, args.pansharpen)

                        if args.upload:
                            try:
                                u = Uploader(args.key, args.secret, args.region)
                            except NoAuthHandlerFound:
                                return ["Could not authenticate with AWS", 1]
                            except URLError:
                                return ["Connection timeout. Probably the region parameter is incorrect", 1]
                            u.run(args.bucket, get_file(stored), stored)

                        return ["The output is stored at %s" % stored]
                    else:
                        return ['Download Completed', 0]
            except IncorrectSceneId:
                return ['The SceneID provided was incorrect', 1]


def process_image(path, bands=None, verbose=False, pansharpen=False):
    try:
        bands = convert_to_integer_list(bands)
        p = Process(path, bands=bands, verbose=verbose)
    except IOError:
        exit("Zip file corrupted", 1)
    except FileDoesNotExist as e:
        exit(e.message, 1)

    return p.run(pansharpen)


def __main__():

    global parser
    parser = args_options()
    args = parser.parse_args()
    with timer():
        exit(*main(args))

if __name__ == "__main__":
    try:
        __main__()
    except (KeyboardInterrupt, pycurl.error):
        exit('Received Ctrl + C... Exiting! Bye.', 1)
