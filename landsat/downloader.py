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


class Downloader(VerbosityMixin):

    def __init__(self, verbose=False):
        self.download_dir = settings.DOWNLOAD_DIR
        self.google = 'https://storage.googleapis.com/earthengine-public/landsat/'
        self.s3 = 'https://landsat-pds.s3.amazonaws.com/'

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
                if bands:
                    if isinstance(bands, list):
                        # Create a folder to download the specific bands into
                        path = check_create_folder(join(self.download_dir, scene))
                        for band in bands:
                            self._amazon_s3(scene, band, path)
                    else:
                        raise Exception('Expected bands list')
                else:
                    self._google_storage(scene, self.download_dir)

        else:
            raise Exception('Expected sceneIDs list')

    def _google_storage(self, scene, path):
        """ Google Storage Downloader """
        sat = self._scene_intrepreter(scene)

        filename = scene + '.tar.bz'
        url = join(self.google, sat['sat'], sat['path'], sat['row'], filename)

        if self._remote_file_exists(url):
            self._fetch(url, path, filename)

        else:
            RemoteFileDoesntExist('%s is not available on Google Storage' % filename)

    def _amazon_s3(self, scene, band, path):
        """ Amazon S3 downloader """
        sat = self._scene_intrepreter(scene)

        filename = '%s_B%s.TIF' % (scene, band)
        url = join(self.s3, sat['sat'], sat['path'], sat['row'], scene, filename)

        if self._remote_file_exists(url):
            self._fetch(url, path, filename)

        else:
            RemoteFileDoesntExist('%s is not available on Amazon S3' % filename)

    def _fetch(self, url, path, filename):

        self.output('Downloading: %s' % filename, normal=True, arrow=True)

        if exists(join(path, filename)):
            size = getsize(join(path, filename))
            headers = requests.head(url).headers
            if size == int(headers['content-length']):
                self.output('%s already exists on your system' % filename, normal=True, color='green', indent=1)
                return

        fetch(url, path)
        self.output('stored at %s' % path, normal=True, color='green', indent=1)

    def _remote_file_exists(self, url):
        status = requests.head(url).status_code

        if status == 200:
            return True
        else:
            return False

    def _scene_intrepreter(self, scene):
        """ Conver sceneID to rows, paths and dates """
        anatomy = {
            'path': None,
            'row': None,
            'sat': None,
        }
        if isinstance(scene, str) and len(scene) == 21:
            anatomy['path'] = scene[3:6]
            anatomy['row'] = scene[6:9]
            anatomy['sat'] = 'L' + scene[2:3]

            return anatomy
        else:
            raise Exception('Received incorrect scene')


if __name__ == '__main__':

    d = Downloader()

    # d.download(['LC81990242015046LGN00', 'LC80030172015001LGN00'])
    d.download(['LC80030172015001LGN00'], bands=[5, 4])
