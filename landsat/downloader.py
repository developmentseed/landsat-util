# Landsat Util
# License: CC0 1.0 Universal
from os.path import join, exists, getsize

from homura import download as fetch
import requests

from utils import check_create_folder
from mixins import VerbosityMixin
import settings


class RemoteFileDoesntExist(Exception):
    pass


class IncorrectSceneId(Exception):
    pass


class Downloader(VerbosityMixin):

    def __init__(self, verbose=False, download_dir=None):
        self.download_dir = download_dir if download_dir else settings.DOWNLOAD_DIR
        self.google = settings.GOOGLE_STORAGE
        self.s3 = settings.S3_LANDSAT

        # Make sure download directory exist
        check_create_folder(self.download_dir)

    def download(self, scenes, bands=None):
        """
        Download scenese from Google Storage or Amazon S3 if bands are provided

        @params
        scenes - A list of sceneIDs
        bands - A list of bands
        """

        if isinstance(scenes, list):
            for scene in scenes:
                # If bands are provided the image is from 2015 or later use Amazon
                if (bands and int(scene[12]) > 4):
                    if isinstance(bands, list):
                        # Create a folder to download the specific bands into
                        path = check_create_folder(join(self.download_dir, scene))
                        try:
                            # Always grab MTL.txt if bands are specified
                            bands_plus = bands
                            bands_plus.append('MTL')
                            for band in bands_plus:
                                self.amazon_s3(scene, band, path)
                        except RemoteFileDoesntExist:
                            self.google_storage(scene, self.download_dir)
                    else:
                        raise Exception('Expected bands list')
                else:
                    self.google_storage(scene, self.download_dir)

            return True

        else:
            raise Exception('Expected sceneIDs list')

    def google_storage(self, scene, path):
        """ Google Storage Downloader """
        sat = self.scene_interpreter(scene)

        filename = scene + '.tar.bz'
        url = self.google_storage_url(sat)

        if self.remote_file_exists(url):
            return self.fetch(url, path, filename)

        else:
            raise RemoteFileDoesntExist('%s is not available on Google Storage' % filename)

    def amazon_s3(self, scene, band, path):
        """ Amazon S3 downloader """
        sat = self.scene_interpreter(scene)

        if band != 'MTL':
            filename = '%s_B%s.TIF' % (scene, band)
        else:
            filename = '%s_%s.txt' % (scene, band)
        url = self.amazon_s3_url(sat, filename)

        if self.remote_file_exists(url):
            return self.fetch(url, path, filename)

        else:
            raise RemoteFileDoesntExist('%s is not available on Amazon S3' % filename)

    def fetch(self, url, path, filename):

        self.output('Downloading: %s' % filename, normal=True, arrow=True)

        if exists(join(path, filename)):
            size = getsize(join(path, filename))
            if size == self.get_remote_file_size(url):
                self.output('%s already exists on your system' % filename, normal=True, color='green', indent=1)
                return False

        fetch(url, path)
        self.output('stored at %s' % path, normal=True, color='green', indent=1)

        return True

    def google_storage_url(self, sat):
        """
        Return a google storage url the contains the scene provided
        @params
        sat - expects an object created by scene_interpreter method
        """
        filename = sat['scene'] + '.tar.bz'
        return join(self.google, sat['sat'], sat['path'], sat['row'], filename)

    def amazon_s3_url(self, sat, filename):
        """
        Return an amazon s3 url the contains the scene and band provided
        @params
        sat - expects an object created by scene_interpreter method
        """
        return join(self.s3, sat['sat'], sat['path'], sat['row'], sat['scene'], filename)

    def remote_file_exists(self, url):
        status = requests.head(url).status_code

        if status == 200:
            return True
        else:
            return False

    def get_remote_file_size(self, url):
        """ Gets the filesize of a remote file """
        headers = requests.head(url).headers
        return int(headers['content-length'])

    def scene_interpreter(self, scene):
        """ Conver sceneID to rows, paths and dates """
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
    d.download(['LC80030172015001LGN00'], bands=[5, 4])
