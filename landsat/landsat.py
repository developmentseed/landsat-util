#!/usr/bin/env python

# Landsat Util
# License: CC0 1.0 Universal

from __future__ import print_function, division, absolute_import

import argparse
import textwrap
import json
from os.path import join

try:
    from urllib.request import URLError
except ImportError:
    from urllib2 import URLError

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import pycurl
from boto.exception import NoAuthHandlerFound

from .downloader import Downloader, IncorrectSceneId, RemoteFileDoesntExist, USGSInventoryAccessMissing
from .search import Search
from .uploader import Uploader
from .utils import reformat_date, convert_to_integer_list, timer, exit, get_file, convert_to_float_list
from .mixins import VerbosityMixin
from .image import Simple, PanSharpen, FileDoesNotExist
from .ndvi import NDVIWithManualColorMap, NDVI
from .__init__ import __version__
from . import settings


DESCRIPTION = """Landsat-util is a command line utility that makes it easy to
search, download, and process Landsat imagery.

    Commands:
        Search:
            landsat.py search [-p --pathrow] [--lat] [--lon] [--address] [-l LIMIT] [-s START] [-e END] [-c CLOUD]
                              [-h]

            optional arguments:
                -p, --pathrow       Paths and Rows in order separated by comma. Use quotes "001,003".
                                    Example: path,row,path,row 001,001,190,204

                --lat               Latitude

                --lon               Longitude

                --address           Street address

                -l LIMIT, --limit LIMIT
                                    Search return results limit default is 10

                -s START, --start START
                                    Start Date - Most formats are accepted e.g.
                                    Jun 12 2014 OR 06/12/2014

                -e END, --end END   End Date - Most formats are accepted e.g.
                                    Jun 12 2014 OR 06/12/2014

                --latest N          Returns the N latest images within the last 365 days.

                -c CLOUD, --cloud CLOUD
                                    Maximum cloud percentage. Default: 20 perct

                --json              Returns a bare JSON response

                --geojson           Returns a geojson response

                -h, --help          Show this help message and exit

        Download:
            landsat download sceneID [sceneID ...] [-h] [-b --bands]

            positional arguments:
                sceneID     Provide Full sceneIDs. You can add as many sceneIDs as you wish

                Example: landsat download LC81660392014196LGN00

            optional arguments:
                -b --bands          If you specify bands, landsat-util will try to download the band from S3.
                                    If the band does not exist, an error is returned

                -h, --help          Show this help message and exit

                -d, --dest          Destination path

                -p, --process       Process the image after download

                --pansharpen        Whether to also pansharpen the processed image.
                                    Pansharpening requires larger memory

                --ndvi              Calculates NDVI and produce a RGB GTiff with separate colorbar.

                --ndvigrey          Calculates NDVI and produce a greyscale GTiff.

                --clip              Clip the image with the bounding box provided. Values must be in WGS84 datum,
                                    and with longitude and latitude units of decimal degrees separated by comma.
                                    Example: --clip=-346.06658935546875,49.93531194616915,-345.4595947265625,
                                    50.2682767372753

                -u --upload         Upload to S3 after the image processing completed

                --key               Amazon S3 Access Key (You can also be set AWS_ACCESS_KEY_ID as
                                    Environment Variables)

                --secret            Amazon S3 Secret Key (You can also be set AWS_SECRET_ACCESS_KEY as
                                    Environment Variables)

                --bucket            Bucket name (required if uploading to s3)

                --region            URL to S3 region e.g. s3-us-west-2.amazonaws.com

                --force-unzip       Force unzip tar file

                --username          USGS Eros account Username (only works if the account has special
                                    inventory access). Username and password as a fallback if the image
                                    is not found on AWS S3 or Google Storage

                --password          USGS Eros account Password

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

                --ndvi              Calculates NDVI and produce a RGB GTiff with separate colorbar.

                --ndvigrey          Calculates NDVI and produce a greyscale GTiff.

                --clip              Clip the image with the bounding box provided. Values must be in WGS84 datum,
                                    and with longitude and latitude units of decimal degrees separated by comma.
                                    Example: --clip=-346.06658935546875,49.93531194616915,-345.4595947265625,
                                    50.2682767372753

                -v, --verbose       Show verbose output

                -h, --help          Show this help message and exit

                -u --upload         Upload to S3 after the image processing completed

                --key               Amazon S3 Access Key (You can also be set AWS_ACCESS_KEY_ID as
                                    Environment Variables)

                --secret            Amazon S3 Secret Key (You can also be set AWS_SECRET_ACCESS_KEY as
                                    Environment Variables)

                --bucket            Bucket name (required if uploading to s3)

                --region            URL to S3 region e.g. s3-us-west-2.amazonaws.com

                --force-unzip       Force unzip tar file
"""


def args_options():
    """ Generates an arugment parser.

    :returns:
        Parser object
    """

    parser = argparse.ArgumentParser(prog='landsat',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent(DESCRIPTION))

    subparsers = parser.add_subparsers(help='Landsat Utility',
                                       dest='subs')

    parser.add_argument('--version', action='version', version='%(prog)s version ' + __version__)

    # Search Logic
    parser_search = subparsers.add_parser('search',
                                          help='Search Landsat metadata')

    # Global search options
    parser_search.add_argument('-l', '--limit', default=10, type=int,
                               help='Search return results limit\n'
                               'default is 10')
    parser_search.add_argument('-s', '--start',
                               help='Start Date - Most formats are accepted '
                               'e.g. Jun 12 2014 OR 06/12/2014')
    parser_search.add_argument('-e', '--end',
                               help='End Date - Most formats are accepted '
                               'e.g. Jun 12 2014 OR 06/12/2014')
    parser_search.add_argument('--latest', default=-1, type=int,
                               help='returns the N latest images within the last 365 days')
    parser_search.add_argument('-c', '--cloud', type=float, default=100.0,
                               help='Maximum cloud percentage '
                               'default is 100 perct')
    parser_search.add_argument('-p', '--pathrow',
                               help='Paths and Rows in order separated by comma. Use quotes ("001").'
                               'Example: path,row,path,row 001,001,190,204')
    parser_search.add_argument('--lat', type=float, help='The latitude')
    parser_search.add_argument('--lon', type=float, help='The longitude')
    parser_search.add_argument('--address', type=str, help='The address')
    parser_search.add_argument('--json', action='store_true', help='Returns a bare JSON response')
    parser_search.add_argument('--geojson', action='store_true', help='Returns a geojson response')

    parser_download = subparsers.add_parser('download',
                                            help='Download images from Google Storage')
    parser_download.add_argument('scenes',
                                 metavar='sceneID',
                                 nargs="+",
                                 help="Provide Full sceneID, e.g. LC81660392014196LGN00")

    parser_download.add_argument('-b', '--bands', help='If you specify bands, landsat-util will try to download '
                                 'the band from S3. If the band does not exist, an error is returned', default=None)
    parser_download.add_argument('-d', '--dest', help='Destination path')
    parser_download.add_argument('-p', '--process', help='Process the image after download', action='store_true')
    parser_download.add_argument('--pansharpen', action='store_true',
                                 help='Whether to also pansharpen the process '
                                 'image. Pansharpening requires larger memory')
    parser_download.add_argument('--ndvi', action='store_true',
                                 help='Whether to run the NDVI process. If used, bands parameter is disregarded')
    parser_download.add_argument('--ndvigrey', action='store_true', help='Create an NDVI map in grayscale (grey)')
    parser_download.add_argument('--clip', help='Clip the image with the bounding box provided. Values must be in ' +
                                 'WGS84 datum, and with longitude and latitude units of decimal degrees ' +
                                 'separated by comma.' +
                                 'Example: --clip=-346.06658935546875,49.93531194616915,-345.4595947265625,' +
                                 '50.2682767372753')
    parser_download.add_argument('-u', '--upload', action='store_true',
                                 help='Upload to S3 after the image processing completed')
    parser_download.add_argument('--username', help='USGS Eros account Username (only works if the account has' +
                                 ' special inventory access). Username and password as a fallback if the image' +
                                 'is not found on AWS S3 or Google Storage')
    parser_download.add_argument('--password', help='USGS Eros username, used as a fallback')
    parser_download.add_argument('--key', help='Amazon S3 Access Key (You can also be set AWS_ACCESS_KEY_ID as '
                                 'Environment Variables)')
    parser_download.add_argument('--secret', help='Amazon S3 Secret Key (You can also be set AWS_SECRET_ACCESS_KEY '
                                 'as Environment Variables)')
    parser_download.add_argument('--bucket', help='Bucket name (required if uploading to s3)')
    parser_download.add_argument('--region', help='URL to S3 region e.g. s3-us-west-2.amazonaws.com')
    parser_download.add_argument('--force-unzip', help='Force unzip tar file', action='store_true')

    parser_process = subparsers.add_parser('process', help='Process Landsat imagery')
    parser_process.add_argument('path',
                                help='Path to the compressed image file')
    parser_process.add_argument('--pansharpen', action='store_true',
                                help='Whether to also pansharpen the process '
                                'image. Pansharpening requires larger memory')
    parser_process.add_argument('--ndvi', action='store_true', help='Create an NDVI map in color.')
    parser_process.add_argument('--ndvigrey', action='store_true', help='Create an NDVI map in grayscale (grey)')
    parser_process.add_argument('--clip', help='Clip the image with the bounding box provided. Values must be in ' +
                                'WGS84 datum, and with longitude and latitude units of decimal degrees ' +
                                'separated by comma.' +
                                'Example: --clip=-346.06658935546875,49.93531194616915,-345.4595947265625,' +
                                '50.2682767372753')
    parser_process.add_argument('-b', '--bands', help='specify band combinations. Default is 432'
                                'Example: --bands 321', default='432')
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
    parser_process.add_argument('--force-unzip', help='Force unzip tar file', action='store_true')

    return parser


def main(args):
    """
    Main function - launches the program.

    :param args:
        The Parser arguments
    :type args:
        Parser object

    :returns:
        List

    :example:
        >>> ["The latitude and longitude values must be valid numbers", 1]
    """

    v = VerbosityMixin()

    if args:

        if 'clip' in args:
            bounds = convert_to_float_list(args.clip)
        else:
            bounds = None

        if args.subs == 'process':
            verbose = True if args.verbose else False
            force_unzip = True if args.force_unzip else False
            stored = process_image(args.path, args.bands, verbose, args.pansharpen, args.ndvi, force_unzip,
                                   args.ndvigrey, bounds)

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
                if args.latest > 0:
                    args.limit = 25
                    end = datetime.now()
                    start = end - relativedelta(days=+365)
                    args.end = end.strftime("%Y-%m-%d")
                    args.start = start.strftime("%Y-%m-%d")
            except (TypeError, ValueError):
                return ["Your date format is incorrect. Please try again!", 1]

            s = Search()

            try:
                if args.lat is not None:
                    lat = float(args.lat)
                else:
                    lat = None

                if args.lon is not None:
                    lon = float(args.lon)
                else:
                    lon = None
            except ValueError:
                return ["The latitude and longitude values must be valid numbers", 1]

            address = args.address
            if address and (lat and lon):
                return ["Cannot specify both address and latitude-longitude"]

            result = s.search(paths_rows=args.pathrow,
                              lat=lat,
                              lon=lon,
                              address=address,
                              limit=args.limit,
                              start_date=args.start,
                              end_date=args.end,
                              cloud_max=args.cloud,
                              geojson=args.geojson)

            if 'status' in result:

                if result['status'] == 'SUCCESS':
                    if args.json:
                        return json.dumps(result)

                    if args.latest > 0:
                        datelist = []
                        for i in range(0, result['total_returned']):
                            datelist.append((result['results'][i]['date'], result['results'][i]))

                        datelist.sort(key=lambda tup: tup[0], reverse=True)
                        datelist = datelist[:args.latest]

                        result['results'] = []
                        for i in range(0, len(datelist)):
                            result['results'].append(datelist[i][1])
                            result['total_returned'] = len(datelist)

                    else:
                        v.output('%s items were found' % result['total'], normal=True, arrow=True)

                    if result['total'] > 100:
                        return ['Over 100 results. Please narrow your search', 1]
                    else:
                        v.output(json.dumps(result, sort_keys=True, indent=4), normal=True, color='green')
                    return ['Search completed!']

                elif result['status'] == 'error':
                    return [result['message'], 1]

            if args.geojson:
                return json.dumps(result)

        elif args.subs == 'download':
            d = Downloader(download_dir=args.dest, usgs_user=args.username, usgs_pass=args.password)
            try:
                bands = convert_to_integer_list(args.bands)

                if args.process:
                    if args.pansharpen:
                        bands.append(8)

                    if args.ndvi or args.ndvigrey:
                        bands = [4, 5]

                    if not args.bands:
                        bands = [4, 3, 2]

                files = d.download(args.scenes, bands)

                if args.process:
                    if not args.bands:
                        args.bands = '432'
                    force_unzip = True if args.force_unzip else False
                    for f in files:
                        stored = process_image(f, args.bands, False, args.pansharpen, args.ndvi, force_unzip,
                                               args.ndvigrey, bounds=bounds)

                        if args.upload:
                            try:
                                u = Uploader(args.key, args.secret, args.region)
                            except NoAuthHandlerFound:
                                return ["Could not authenticate with AWS", 1]
                            except URLError:
                                return ["Connection timeout. Probably the region parameter is incorrect", 1]
                            u.run(args.bucket, get_file(stored), stored)

                    return ['The output is stored at %s' % stored, 0]
                else:
                    return ['Download Completed', 0]
            except IncorrectSceneId:
                return ['The SceneID provided was incorrect', 1]
            except (RemoteFileDoesntExist, USGSInventoryAccessMissing) as e:
                return [e.message, 1]


def process_image(path, bands=None, verbose=False, pansharpen=False, ndvi=False, force_unzip=None,
                  ndvigrey=False, bounds=None):
    """ Handles constructing and image process.

    :param path:
        The path to the image that has to be processed
    :type path:
        String
    :param bands:
        List of bands that has to be processed. (optional)
    :type bands:
        List
    :param verbose:
        Sets the level of verbosity. Default is False.
    :type verbose:
        boolean
    :param pansharpen:
        Whether to pansharpen the image. Default is False.
    :type pansharpen:
        boolean

    :returns:
        (String) path to the processed image
    """
    try:
        bands = convert_to_integer_list(bands)
        if pansharpen:
            p = PanSharpen(path, bands=bands, dst_path=settings.PROCESSED_IMAGE,
                           verbose=verbose, force_unzip=force_unzip, bounds=bounds)
        elif ndvigrey:
            p = NDVI(path, verbose=verbose, dst_path=settings.PROCESSED_IMAGE, force_unzip=force_unzip, bounds=bounds)
        elif ndvi:
            p = NDVIWithManualColorMap(path, dst_path=settings.PROCESSED_IMAGE,
                                       verbose=verbose, force_unzip=force_unzip, bounds=bounds)
        else:
            p = Simple(path, bands=bands, dst_path=settings.PROCESSED_IMAGE, verbose=verbose, force_unzip=force_unzip,
                       bounds=bounds)

    except IOError as err:
        exit(str(err), 1)
    except FileDoesNotExist as err:
        exit(str(err), 1)

    return p.run()


def __main__():

    global parser
    parser = args_options()
    args = parser.parse_args()
    if args.subs == 'search' and (hasattr(args, 'json') or hasattr(args, 'geojson')):
            print(main(args))
    else:
        with timer():
            exit(*main(args))

if __name__ == "__main__":
    try:
        __main__()
    except (KeyboardInterrupt, pycurl.error):
        exit('Received Ctrl + C... Exiting! Bye.', 1)
