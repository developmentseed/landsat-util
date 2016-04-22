from __future__ import print_function, division, absolute_import

from os.path import join

import rasterio
import numpy

from . import settings
from .decorators import rasterio_decorator
from .image import BaseProcess


class NDVI(BaseProcess):

    def __init__(self, path, bands=None, **kwargs):
        bands = [4, 5]
        self._read_cmap()
        super(NDVI, self).__init__(path, bands, **kwargs)

    def _read_cmap(self):
        """
        reads the colormap from a text file given in settings.py.
        See colormap_cubehelix.txt. File must contain 256 RGB values
        """

        try:
            i = 0
            colormap = {0: (0, 0, 0)}
            with open(settings.COLORMAP) as cmap:
                lines = cmap.readlines()
                for line in lines:
                    if i == 0 and 'mode = ' in line:
                        i = 1
                        maxval = float(line.replace('mode = ', ''))
                    elif i > 0:
                        str = line.split()
                        if str == []:  # when there are empty lines at the end of the file
                            break
                        colormap.update(
                            {
                                i: (int(round(float(str[0]) * 255 / maxval)),
                                    int(round(float(str[1]) * 255 / maxval)),
                                    int(round(float(str[2]) * 255 / maxval)))
                            }
                        )
                        i += 1
        except IOError:
            pass

        self.cmap = {k: v[:4] for k, v in colormap.items()}

    @rasterio_decorator
    def run(self):
        """
        Executes NDVI processing
        """
        self.output("* NDVI processing started.", normal=True)

        bands = self._read_bands()
        image_data = self._get_image_data()

        new_bands = []
        for i in range(0, 2):
            new_bands.append(numpy.empty(image_data['shape'], dtype=numpy.float32))

        self._warp(image_data, bands, new_bands)

        # Bands are no longer needed
        del bands

        calc_band = numpy.true_divide((new_bands[1] - new_bands[0]), (new_bands[1] + new_bands[0]))

        output_band = numpy.rint((calc_band + 1) * 255 / 2).astype(numpy.uint8)

        output_file = join(self.dst_path, self._filename(suffix='NDVI'))

        return self.write_band(output_band, output_file, image_data)

    def write_band(self, output_band, output_file, image_data):

        # from http://publiclab.org/notes/cfastie/08-26-2014/new-ndvi-colormap
        with rasterio.open(output_file, 'w', driver='GTiff',
                           width=image_data['shape'][1],
                           height=image_data['shape'][0],
                           count=1,
                           dtype=numpy.uint8,
                           nodata=0,
                           transform=image_data['dst_transform'],
                           crs=self.dst_crs) as output:

            output.write_band(1, output_band)

            self.output("Writing to file", normal=True, color='green', indent=1)
        return output_file


class NDVIWithManualColorMap(NDVI):

    def manual_colormap(self, n, i):
        return self.cmap[n][i]

    def write_band(self, output_band, output_file, image_data):
        # colormaps will overwrite our transparency masks so we will manually
        # create three RGB bands

        self.output("Applying ColorMap", normal=True, arrow=True)
        self.cmap[0] = (0, 0, 0, 255)

        v_manual_colormap = numpy.vectorize(self.manual_colormap, otypes=[numpy.uint8])
        rgb_bands = []
        for i in range(3):
            rgb_bands.append(v_manual_colormap(output_band, i))

        with rasterio.drivers(GDAL_TIFF_INTERNAL_MASK=True):
            with rasterio.open(output_file, 'w', driver='GTiff',
                               width=image_data['shape'][1],
                               height=image_data['shape'][0],
                               count=3,
                               dtype=numpy.uint8,
                               nodata=0,
                               photometric='RGB',
                               transform=image_data['dst_transform'],
                               crs=self.dst_crs) as output:

                for i in range(3):
                    output.write_band(i + 1, rgb_bands[i])

            self.output("Writing to file", normal=True, color='green', indent=1)
        return output_file
