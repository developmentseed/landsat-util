# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco
#
# License: CC0 1.0 Universal

import os
import re

import ogr2ogr
import settings
import ogrinfo
from general_helper import Capturing, check_create_folder

# creates new input-shp.shp and ASSIGNS spatial reference system
# ogr2ogr.main(['', '-a_srs', 'EPSG:4326', 'custom-sh-copy.shp',
# '%s/draft-scripts/sample/custom-test.shp' % settings.BASE_DIR])


class Clipper(object):

    def __init__(self):
        self.assests_dir = settings.ASSESTS_DIR
        self.shapefile_output = settings.SHAPEFILE_OUTPUT
        self.shapefile_input = settings.SHAPEFILE_INPUT

        check_create_folder(self.shapefile_input)
        check_create_folder(self.shapefile_output)

    def shapefile(self, file):
        self.__srs_adjustment(file, 'a')
        self.__srs_adjustment(file, 't')
        self.__clip_shapefile(file)
        self.__generate_path_row('landsat-tiles.shp', 'landsat-tiles')

    def country(self, name):
        self.__extract_country(name)
        self.__clip_shapefile('country.shp')
        self.__generate_path_row('landsat-tiles.shp', 'landsat-tiles')

    def __srs_adjustment(self, file, load='a', type='EPSG:4326'):
        print "Executing SRS adjustments"

        input = '%s/%s' % (self.shapefile_input, file)
        output = '%s/%s' % (self.shapefile_output, file)
        argv = ['', '-%s_srs' % load, type, os.path.dirname(output), input]

        if os.path.isfile(output):
            input = output
            argv.insert(1, '-overwrite')

        ogr2ogr.main(argv)

    def __extract_country(self, name):
        print "Extracting the country"

        input = '%s/ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp' % \
                self.assests_dir
        output = '%s/country.shp' % self.shapefile_output
        argv = ['', '-where', 'admin like "%s" or adm0_a3 like "%s"' %
                (name, name), output, input]

        if os.path.isfile(output):
            argv.insert(1, '-overwrite')

        ogr2ogr.main(argv)

    def __clip_shapefile(self, file):
        print "Clipping the shapefile"

        clipper = '%s/%s' % (self.shapefile_output, file)
        output = '%s/landsat-tiles.shp' % self.shapefile_output
        input = '%s/wrs2_descending/wrs2_descending.shp' % self.assests_dir
        argv = ['', '-clipsrc', clipper, output, input]

        if os.path.isfile(output):
            argv.insert(1, '-overwrite')

        ogr2ogr.main(argv)

    def __generate_path_row(self, source, layer=''):
        print "Generating paths and rows"

        source = self.shapefile_output + '/' + source
        with Capturing() as output:
            ogrinfo.main(
                ['',
                 '-sql',
                 'SELECT PATH, ROW FROM "%s"' % layer, source, layer
                 ])

        # Convert the above output into a list with rows and paths
        rp = [re.sub(r'([A-Z]|[a-z]|\s|\(|\)|\'|\"|=|,|:|\.0|\.)', '', a)
              for a in str(output).split(',') if 'ROW' in a or 'PATH' in a]
        for k, v in enumerate(rp):
            if len(v) == 1:
                rp[k] = '00%s' % v
            elif len(v) == 2:
                rp[k] = '0%s' % v

        s = open('%s/rows_paths.txt' % (self.shapefile_output), 'w')
        s.write(','.join(rp))
        s.close()

        print ','.join(rp)
