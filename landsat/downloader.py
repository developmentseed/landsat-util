# Landsat Util
# License: CC0 1.0 Universal

from __future__ import print_function, division, absolute_import

from xml.etree import ElementTree
from os.path import join, exists, getsize

import requests
from usgs import api, USGSError
from homura import download as fetch

from .utils import check_create_folder, url_builder
from .mixins import VerbosityMixin
from . import settings


class RemoteFileDoesntExist(Exception):
    """ Exception to be used when the remote file does not exist """
    pass


class IncorrectSceneId(Exception):
    """ Exception to be used when scene id is incorrect """
    pass


class USGSInventoryAccessMissing(Exception):
    """ Exception for when User does not have Inventory Service access """
    pass


class Downloader(VerbosityMixin):
    """ The downloader class """

    def __init__(self, verbose=False, download_dir=None, usgs_user=None, usgs_pass=None):
        self.download_dir = download_dir if download_dir else settings.DOWNLOAD_DIR
        self.google = settings.GOOGLE_STORAGE
        self.s3 = settings.S3_LANDSAT
        self.usgs_user = usgs_user
        self.usgs_pass = usgs_pass

        # Make sure download directory exist
        check_create_folder(self.download_dir)

    def download(self, scenes, bands=None):
        """
        Download scenese from Google Storage or Amazon S3 if bands are provided

        :param scenes:
            A list of scene IDs
        :type scenes:
            List
        :param bands:
            A list of bands. Default value is None.
        :type scenes:
            List

        :returns:
            (List) includes downloaded scenes as key and source as value (aws or google)
        """

        if isinstance(scenes, list):
            files = []

            for scene in scenes:

                # for all scenes if bands provided, first check AWS, if the bands exist
                # download them, otherwise use Google and then USGS.
                try:
                    # if bands are not provided, directly go to Goodle and then USGS
                    if not isinstance(bands, list):
                        raise RemoteFileDoesntExist
                    files.append(self.amazon_s3(scene, bands))

                except RemoteFileDoesntExist:
                    try:
                        files.append(self.google_storage(scene, self.download_dir))
                    except RemoteFileDoesntExist:
                        files.append(self.usgs_eros(scene, self.download_dir))

            return files

        else:
            raise Exception('Expected sceneIDs list')

    def usgs_eros(self, scene, path):
        """ Downloads the image from USGS """

        # download from usgs if login information is provided
        if self.usgs_user and self.usgs_pass:
            try:
                api_key = api.login(self.usgs_user, self.usgs_pass)
            except USGSError as e:
                error_tree = ElementTree.fromstring(str(e.message))
                error_text = error_tree.find("SOAP-ENV:Body/SOAP-ENV:Fault/faultstring", api.NAMESPACES).text
                raise USGSInventoryAccessMissing(error_text)

            download_url = api.download('LANDSAT_8', 'EE', [scene], api_key=api_key)
            if download_url:
                self.output('Source: USGS EarthExplorer', normal=True, arrow=True)
                return self.fetch(download_url[0], path)

            raise RemoteFileDoesntExist('%s is not available on AWS S3, Google or USGS Earth Explorer' % scene)
        raise RemoteFileDoesntExist('%s is not available on AWS S3 or Google Storage' % scene)

    def google_storage(self, scene, path):
        """
        Google Storage Downloader.

        :param scene:
            The scene id
        :type scene:
            String
        :param path:
            The directory path to where the image should be stored
        :type path:
            String

        :returns:
            Boolean
        """

        sat = self.scene_interpreter(scene)
        url = self.google_storage_url(sat)

        self.remote_file_exists(url)

        self.output('Source: Google Storage', normal=True, arrow=True)
        return self.fetch(url, path)

    def amazon_s3(self, scene, bands):
        """
        Amazon S3 downloader
        """

        sat = self.scene_interpreter(scene)

        # Always grab MTL.txt and QA band if bands are specified
        if 'BQA' not in bands:
            bands.append('QA')

        if 'MTL' not in bands:
            bands.append('MTL')

        urls = []

        for band in bands:
            # get url for the band
            url = self.amazon_s3_url(sat, band)

            # make sure it exist
            self.remote_file_exists(url)
            urls.append(url)

        # create folder
        path = check_create_folder(join(self.download_dir, scene))

        self.output('Source: AWS S3', normal=True, arrow=True)
        for url in urls:
            self.fetch(url, path)

        return path

    def fetch(self, url, path):
        """ Downloads the given url.

        :param url:
            The url to be downloaded.
        :type url:
            String
        :param path:
            The directory path to where the image should be stored
        :type path:
            String
        :param filename:
            The filename that has to be downloaded
        :type filename:
            String

        :returns:
            Boolean
        """

        segments = url.split('/')
        filename = segments[-1]

        # remove query parameters from the filename
        filename = filename.split('?')[0]

        self.output('Downloading: %s' % filename, normal=True, arrow=True)

        # print(join(path, filename))
        # raise Exception
        if exists(join(path, filename)):
            size = getsize(join(path, filename))
            if size == self.get_remote_file_size(url):
                self.output('%s already exists on your system' % filename, normal=True, color='green', indent=1)

        else:
            fetch(url, path)
        self.output('stored at %s' % path, normal=True, color='green', indent=1)

        return join(path, filename)

    def google_storage_url(self, sat):
        """
        Returns a google storage url the contains the scene provided.

        :param sat:
            Expects an object created by scene_interpreter method
        :type sat:
            dict

        :returns:
            (String) The URL to a google storage file
        """
        filename = sat['scene'] + '.tar.bz'
        return url_builder([self.google, sat['sat'], sat['path'], sat['row'], filename])

    def amazon_s3_url(self, sat, band):
        """
        Return an amazon s3 url the contains the scene and band provided.

        :param sat:
            Expects an object created by scene_interpreter method
        :type sat:
            dict
        :param filename:
            The filename that has to be downloaded from Amazon
        :type filename:
            String

        :returns:
            (String) The URL to a S3 file
        """
        if band != 'MTL':
            filename = '%s_B%s.TIF' % (sat['scene'], band)
        else:
            filename = '%s_%s.txt' % (sat['scene'], band)

        return url_builder([self.s3, sat['sat'], sat['path'], sat['row'], sat['scene'], filename])

    def remote_file_exists(self, url):
        """ Checks whether the remote file exists.

        :param url:
            The url that has to be checked.
        :type url:
            String

        :returns:
            **True** if remote file exists and **False** if it doesn't exist.
        """
        status = requests.head(url).status_code

        if status != 200:
            raise RemoteFileDoesntExist

    def get_remote_file_size(self, url):
        """ Gets the filesize of a remote file.

        :param url:
            The url that has to be checked.
        :type url:
            String

        :returns:
            int
        """
        headers = requests.head(url).headers
        return int(headers['content-length'])

    def scene_interpreter(self, scene):
        """ Conver sceneID to rows, paths and dates.

        :param scene:
            The scene ID.
        :type scene:
            String

        :returns:
            dict

        :Example output:

        >>> anatomy = {
                'path': None,
                'row': None,
                'sat': None,
                'scene': scene
            }
        """
        anatomy = {
            'path': None,
            'row': None,
            'sat': None,
            'scene': scene
        }
        if isinstance(scene, str) and len(scene) == 21:
            anatomy['path'] = scene[3:6]
            anatomy['row'] = scene[6:9]
            anatomy['sat'] = 'L' + scene[2:3]

            return anatomy
        else:
            raise IncorrectSceneId('Received incorrect scene')


if __name__ == '__main__':

    d = Downloader()

    # d.download(['LC81990242015046LGN00', 'LC80030172015001LGN00'])
