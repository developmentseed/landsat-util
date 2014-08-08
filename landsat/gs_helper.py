# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco
#
# License: CC0 1.0 Universal

import os
import subprocess
from zipfile import ZipFile
import tarfile

from general_helper import check_create_folder


class GsHelper(object):

    def __init__(self, settings):
        self.scene_file_url = settings.SCENE_FILE_URL
        self.download_dir = settings.DOWNLOAD_DIR
        self.zip_dir = settings.ZIP_DIR
        self.unzip_dir = settings.UNZIP_DIR
        self.scene_file = settings.SCENE_FILE
        self.source_url = settings.SOURCE_URL

        # Keep the number of images found on Google search
        # based on the search parameters
        self.found = 0

        check_create_folder(self.download_dir)

    #################
    # Public Methods
    #################

    def search(self, query, date_rng=None):
        files = []
        self.__fetch_gs_scence_list()
        file = open(self.scene_file, 'r')
#       for q in query:
#           print date_rng
        files.extend(
            self.__search_scene_list(scene=file,
                                     query=query,
                                     date_rng=date_rng))

        return files

    def download_single(self, row, path, name, sat_type='L8'):
        url = '%s/%s/%s/%s/%s.tar.bz' % (self.source_url,
                                         sat_type,
                                         path,
                                         row,
                                         name)

        subprocess.call(
            ["gsutil", "cp", "-n", url,
             "%s/%s" % (self.zip_dir, name)])

    def download(self, image_list):
        self.__download_images(image_list)

    def unzip(self):
        self.__unzip_images()

    #################
    # Private Methods
    #################

    def __fetch_gs_scence_list(self):

        if not os.path.isfile(self.scene_file):
            # Download the file
            subprocess.call(
                ["gsutil", "cp", "-n",
                 self.scene_file_url, "%s.zip" % self.scene_file])

            # Unzip the file
            zip = ZipFile('%s.zip' % self.scene_file, 'r')
            zip.extractall(path=self.download_dir)
            zip.close()

            print "scene_file unziped"

#       return open(self.scene_file, 'r')

    def __search_scene_list(self, scene, query, date_rng=None):
        """
        Search scene_list for the provide rows, paths and date range.
        date_rng is a dictionary in this format:
        {
        'start_y': 2014, #year
        'start_jd': 13, #Julian Day
        'end_y': 2014,
        'end_jd': 15, #Julian Day
        }
        """

        file_list = []

        scene.seek(0)
        for line in scene:
            url = line.split('/')
            file_name = url[len(url) - 1]
            f_query = [file_name[3:6], file_name[6:9]]
            jd = int(file_name[13:16].lstrip('0'))  # Julian Day
            year = int(file_name[9:13])

            if f_query in query:
                if date_rng:
                    if year >= date_rng['start_y'] and \
                       year <= date_rng['end_y'] and \
                       jd >= date_rng['start_jd'] and \
                       jd <= date_rng['end_jd']:
                        file_list.append(line.replace('\n', ''))
                        self.found += 1
                else:
                    file_list.append(line.replace('\n', ''))
                    self.found += 1

        print "Search completed! %s images found." % self.found
        return file_list

    def __download_images(self, files):

        check_create_folder(self.zip_dir)

        if self.found > 0:
            print "Downloading %s files from Google Storage..." % self.found

        for url in files:
            url_brk = url.split('/')
            image_name = url_brk[len(url_brk) - 1]
            subprocess.call(
                ["gsutil", "cp", "-n", url,
                 "%s/%s" % (self.zip_dir, image_name)])

    def __unzip_images(self):
        images = os.listdir(self.zip_dir)
        check_create_folder(self.unzip_dir)

        for image in images:
            # Get the image name for creating folder
            image_name = image.split('.')

            if image_name[0] and self.__check_if_not_unzipped(image_name[0]):
                # Create folder
                check_create_folder('%s/%s' % (self.unzip_dir, image_name[0]))

                print "Unzipping %s ...be patient!" % image
                # Unzip
                tar = tarfile.open('%s/%s' % (self.zip_dir, image))
                tar.extractall(path='%s/%s' % (self.unzip_dir, image_name[0]))
                tar.close()

    def __check_if_not_unzipped(self, folder_name):
        if os.path.exists('%s/%s' % (self.unzip_dir, folder_name)):
            print "%s is already unzipped" % folder_name
            return False
        else:
            return True
