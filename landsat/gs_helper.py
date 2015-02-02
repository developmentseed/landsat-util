# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco, KAPPS-
#
# License: CC0 1.0 Universal

import os
import subprocess
from zipfile import ZipFile
import tarfile

from dateutil.parser import parse

from general_helper import (check_create_folder, create_paired_list, exit,
                            Verbosity)
import settings


class GsHelper(object):

    def __init__(self, verbose=False):
        self.scene_file_url = settings.SCENE_FILE_URL
        self.download_dir = settings.DOWNLOAD_DIR
        self.zip_dir = settings.ZIP_DIR
        self.unzip_dir = settings.UNZIP_DIR
        self.scene_file = settings.SCENE_FILE
        self.source_url = settings.SOURCE_URL
        self.verbosity = Verbosity(verbose)

        # Make sure download directory exist
        check_create_folder(self.download_dir)

    def search(self, rows_paths, start=None, end=None):
        """ Search in Landsat's scene_list file. The file is stored as .zip on
        Google Storage and includes the gs url of all available images.

        Example of file information on scene_list.zip:
        gs://earthengine-public/landsat/L8/232/096/LT82320962013127LGN01.tar.bz

        Arguments:
            rows_paths - a string of paired values. e.g. '003,003,001,001'
            start - a string containing the start date. e.g. 12/23/2014
            end - a string containing the end date. e.g. 12/24/2014

        Return:
            a list containing download urls. e.g.:
            ['gs://earthengine-public/landsat/L8/232/094/LT82320942013127LGN01.tar.bz',
             'gs://earthengine-public/landsat/L8/232/093/LT82320932013127LGN01.tar.bz']
        """

        # Turning rows and paths to paired tuples
        try:
            paired = create_paired_list(rows_paths)
        except ValueError, e:
            exit('Error: %s' % e.args[0])

        files = []
        self._fetch_gs_scence_list()
        file = open(self.scene_file, 'r')

        files.extend(self._search_scene_list(scene=file,
                                             query=paired,
                                             start=parse(start),
                                             end=parse(end)))

        return files

    def single_download(self, row, path, name, sat_type='L8'):
        url = '%s/%s/%s/%s/%s.tar.bz' % (self.source_url,
                                         sat_type,
                                         path,
                                         row,
                                         name)
        """ Download single image from Landsat on Google Storage

        Arguments:
            row - string in this format xxx, e.g. 003
            path - string in this format xxx, e.g. 003
            name - zip file name without .tar.bz e.g. LT81360082013127LGN01
            sat_type - e.g. L7, L8, ...
        """
        try:
            subprocess.check_call(
                ["gsutil", "cp", "-n", url, "%s/%s" % (self.zip_dir,
                                                       '%s.tar.bz' % name)])
            return True
        except subprocess.CalledProcessError, subprocess.CommandException:
            return False

    def batch_download(self, image_list):
        """
        Download batch group of images

        Arguments:
            image_list - a list of google storage urls e.g.
                ['gs://earthengine-public/landsat/L8/136/008/'
                      'LT81360082013127LGN01.tar.bz',
                      'gs://earthengine-public/landsat/L8/136/008/'
                      'LT81360082013127LGN01.tar.bz']
        """
        try:
            self._download_images(image_list)
            return True
        except subprocess.CalledProcessError:
            return False

    def extract_row_path(self, scene_name):
        return [scene_name[3:6], scene_name[6:9]]

    def unzip(self):
        """
        Unzip all files stored at settings.ZIP_DIR and save them in
        settings.UNZIP_DIR
        """
        return self._unzip_images()

    #################
    # Private Methods
    #################

    def _fetch_gs_scence_list(self):

        if not os.path.isfile(self.scene_file):
            # Download the file
            self.verbosity.subprocess(["gsutil", "cp", "-n",
                                       self.scene_file_url, "%s.zip" %
                                       self.scene_file])

            # Unzip the file
            zip = ZipFile('%s.zip' % self.scene_file, 'r')
            zip.extractall(path=self.download_dir)
            zip.close()

            self.verbosity.output("scene_file unziped", normal=True, arrow=True)

#       return open(self.scene_file, 'r')

    def _search_scene_list(self, scene, query, start=None, end=None):
        """
        Search scene_list for the provided rows, paths and date range.

        Arguments:
            query - a list of paired tuples e.g.[('003', '003'),('003', '004')]
            start - a datetime object
            end - a datetime object
        """

        file_list = []
        found = 0

        # Query date range
        start_year = start.timetuple().tm_year
        end_year = end.timetuple().tm_year
        start_jd = start.timetuple().tm_yday
        end_jd = end.timetuple().tm_yday

        if start and end:
            self.verbosity.output('Searching for images from %s to %s'
                           % (start.strftime('%b %d, %Y'),
                              end.strftime('%b %d, %Y')), normal=True, arrow=True)

        self.verbosity.output('Rows and Paths searched: ', normal=True, arrow=True)
        self.verbosity.output(query, normal=True)

        scene.seek(0)
        for line in scene:
            url = line.split('/')
            file_name = url[len(url) - 1]
            f_query = [file_name[3:6], file_name[6:9]]
            jd = int(file_name[13:16].lstrip('0'))  # Julian Day
            year = int(file_name[9:13])

            if f_query in query:
                if start and end:
                    if year == start_year and year == end_year:
                        if jd >= start_jd and jd <= end_jd:
                            file_list.append(line.replace('\n', ''))
                            found += 1
                    elif year == start_year:
                        if jd >= start_jd:
                            file_list.append(line.replace('\n', ''))
                            found += 1
                    elif year == end_year:
                        if jd <= end_jd:
                            file_list.append(line.replace('\n', ''))
                            found += 1
                    elif (year > start_year and year < end_year):
                        file_list.append(line.replace('\n', ''))
                        found += 1
                else:
                    file_list.append(line.replace('\n', ''))
                    found += 1

        self.verbosity.output("Search completed! %s images found." % found, normal=True, arrow=True)
        return file_list

    def _download_images(self, files):

        check_create_folder(self.zip_dir)

        self.verbosity.output("Downloading %s files from Google Storage..." % len(files), normal=True, indent=4)

        for url in files:
            url_brk = url.split('/')
            image_name = url_brk[len(url_brk) - 1]
            subprocess.check_call(
                ["gsutil", "cp", "-n", url,
                 "%s/%s" % (self.zip_dir, image_name)])

    def _unzip_images(self):
        images = os.listdir(self.zip_dir)
        check_create_folder(self.unzip_dir)

        for image in images:
            # Get the image name for creating folder
            image_name = image.split('.')

            if image_name[0] and self._check_if_not_unzipped(image_name[0]):
                # Create folder
                check_create_folder('%s/%s' % (self.unzip_dir, image_name[0]))

                self.verbosity.output("Unzipping %s ...be patient!" % image, normal=True, indent=4)
                # Unzip
                tar = tarfile.open('%s/%s' % (self.zip_dir, image))
                tar.extractall(path='%s/%s' % (self.unzip_dir, image_name[0]))
                tar.close()

            return True
        return False

    def _check_if_not_unzipped(self, folder_name):
        if os.path.exists('%s/%s' % (self.unzip_dir, folder_name)):
            self.verbosity.output("%s is already unzipped" % folder_name, normal=True, error=True, indent=4)
            return False
        else:
            return True
