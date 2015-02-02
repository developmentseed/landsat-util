# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco, KAPPS-
#
# License: CC0 1.0 Universal

import os
import re
import errno
import shutil
from tempfile import mkdtemp

from third_party import ogr2ogr
import settings
from third_party import ogrinfo
from general_helper import (Capturing, Verbosity, three_digit,
                            get_file, create_paired_list)


class Clipper(object):

    def __init__(self, verbosity=False):
        self.assests_dir = settings.ASSESTS_DIR
        self.shapefile_output = mkdtemp()
        self.verbosity = Verbosity(verbosity)

    def shapefile(self, file):
        """
        Clip the shapefiles and provide rows and paths

        Attributes:
            file - a string containing the full path to the shapefile
        """

        try:

            self.verbosity.output("Clipping...", normal=True, arrow=True)

            if self.__srs_adjustment(file, 'a'):
                if self.__srs_adjustment(file, 't'):
                    if self.__clip_shapefile(file):
                        rps = self.__generate_path_row('landsat-tiles.shp',
                                                       'landsat-tiles')
                        self._cleanup()
                        return rps
            return False
        except ogr2ogr.OgrError:
            return False

    def country(self, name):
        """
        Provide the rows and paths of the country name provided:

        Attributes:
            name - string of the country name or country alpha-3 code. For
                the full list consult: http://goo.gl/8H9wuq

        Return:
            paired tupiles of paths and rows. e.g. [('145', u'057'),
                                                    ('145', u'058')]
        """

        try:
            self.verbosity.output("Clipping...", normal=True, arrow=True)
            self.__extract_country(name)
            self.__clip_shapefile('country.shp')
            rps = self.__generate_path_row('landsat-tiles.shp', 'landsat-tiles')
            self._cleanup()
            return rps
        except ogr2ogr.OgrError:
            return False

    def _cleanup(self):
        """ Remove temp folder """
        try:
            shutil.rmtree(self.shapefile_output)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

    def __srs_adjustment(self, file, load='a', type='EPSG:4326'):
        """ Run SRS adjustments

        Attributes:
            file - full path to the shapefile
            load - load key, consult ogr2ogr documentation
            type - type key, consult ogr2ogr documentation
        """

        self.verbosity.output("Executing SRS adjustments", normal=True, indent=1)

        output = '%s/%s' % (self.shapefile_output, get_file(file))
        argv = ['', '-%s_srs' % load, type, os.path.dirname(output), file]

        if os.path.isfile(output):
            argv.insert(1, '-overwrite')

        ogr2ogr.main(argv)

        return True

    def __extract_country(self, name):
        """ Create a new country shapefile with rows and paths

        Attributes:
            name - name of the country shapefile name e.g. country.shp
        """

        self.verbosity.output("Extracting the country: %s" % name, normal=True, indent=1)

        input = '%s/ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp' % \
                self.assests_dir
        output = '%s/country.shp' % self.shapefile_output
        argv = ['', '-where', 'admin like "%s" or adm0_a3 like "%s"' %
                (name, name), output, input]

        if os.path.isfile(output):
            argv.insert(1, '-overwrite')

        ogr2ogr.main(argv)

        return True

    def __clip_shapefile(self, file):
        """ Create a new shapefile with rows and paths added to it """
        self.verbosity.output("Clipping the shapefile: %s" % get_file(file), normal=True, indent=1)

        clipper = '%s/%s' % (self.shapefile_output, get_file(file))
        output = '%s/landsat-tiles.shp' % self.shapefile_output
        input = '%s/wrs2_descending/wrs2_descending.shp' % self.assests_dir
        argv = ['', '-clipsrc', clipper, output, input]

        if os.path.isfile(output):
            argv.insert(1, '-overwrite')

        ogr2ogr.main(argv)

        return True

    def __generate_path_row(self, source, layer=''):
        """ Filter rows and paths based on the clipped shapefile """

        self.verbosity.output("Generating paths and rows", normal=True, indent=1)

        source = self.shapefile_output + '/' + source
        with Capturing() as output:
            ogrinfo.main(
                ['',
                 '-sql',
                 'SELECT PATH, ROW FROM "%s"' % layer, source, layer
                 ])

        # Convert the above output into a list with rows and paths
        rp = [re.sub(r'([A-Z]|[a-z]|\s|\(|\)|\'|\"|=|,|:|\.0|\.)', '', a)
              for a in str(output).split(',') if ('ROW' in a or 'PATH' in a)
              and '(3.0)' not in a]

        for k, v in enumerate(rp):
            rp[k] = three_digit(v)

        s = open('%s/rows_paths.txt' % (self.shapefile_output), 'w')
        s.write(','.join(rp))
        s.close()

        self.verbosity.output('The paths and rows are: "%s"' % ','.join(rp), normal=True, indent=1)

        return create_paired_list(rp)
