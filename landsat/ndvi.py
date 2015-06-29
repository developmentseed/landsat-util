import rasterio
from os.path import join
import numpy
from skimage.util import img_as_ubyte

from decorators import rasterio_decorator
from image import BaseProcess


class NDVI(BaseProcess):

    def __init__(self, path, bands=None, dst_path=None, verbose=False, force_unzip=False):
        bands = [4, 5]
        super(NDVI, self).__init__(path, bands, dst_path, verbose, force_unzip)

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

        output_band = numpy.true_divide((new_bands[1] - new_bands[0]), (new_bands[1] + new_bands[0]))

        output_file = '%s_NDVI.TIF' % (self.scene)
        output_file = join(self.dst_path, output_file)

        output = rasterio.open(output_file, 'w', driver='GTiff',
                               width=image_data['shape'][1],
                               height=image_data['shape'][0],
                               count=1,
                               dtype=numpy.uint8,
                               nodata=0,
                               transform=image_data['dst_transform'],
                               crs=self.dst_crs)

        output.write_band(1, img_as_ubyte(output_band))
        self.output("Writing to file", normal=True, color='green', indent=1)
        return output_file
