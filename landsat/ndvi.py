import warnings
from image import BaseProcess
import rasterio
from utils import timer, get_file, check_create_folder
import sys
import settings
from os.path import join
import numpy
from skimage.util import img_as_ubyte


class NDVI(BaseProcess):
    """
    NDVI Processing class

    :param path:
        Path of the image.
    :type path:
        String
    :param verbose:
        Whether the output should be verbose. Default is False. (optional)
    :type verbose:
        boolean
    :param dst_path:
        Path to the folder where the image should be stored. (optional)
    :param force_unzip:
        Whether to force unzip the tar file. Default is False
    :type force_unzip:
        boolean
    """

    def __init__(self, path, force_unzip=False, verbose=False, dst_path=None):
        self.projection = {'init': 'epsg:3857'}
        self.dst_crs = {'init': u'epsg:3857'}
        self.scene = get_file(path).split('.')[0]
        self.bands = [4, 5]

        # Landsat source path
        self.src_path = path.replace(get_file(path), '')

        # Build destination folder if doesn't exist
        self.dst_path = dst_path if dst_path else settings.PROCESSED_IMAGE
        self.dst_path = check_create_folder(join(self.dst_path, self.scene))
        self.verbose = verbose

        # Path to the unzipped folder
        self.scene_path = join(self.src_path, self.scene)

        if self._check_if_zipped(path):
            self._unzip(join(self.src_path, get_file(path)), join(self.src_path, self.scene), self.scene, force_unzip)

        self.bands_path = []
        for band in self.bands:
            self.bands_path.append(join(self.scene_path, self._get_full_filename(band)))

    def run(self):
        """
        Executes NDVI processing
        """
        self.output("* NDVI processing started.", normal=True)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with rasterio.drivers():
                bands = []
                try:
                    for i, band in enumerate(self.bands):
                        bands.append(self._read_band(self.bands_path[i]))

                except IOError as e:
                    exit(e.message, 1)

                src = rasterio.open(self.bands_path[-1])
                self.pixel = src.affine[0]

                proj_data = {
                    'transform': src.transform,
                    'crs': src.crs,
                    'affine': src.affine,
                    'shape': src.shape
                }
                crn = self._get_boundaries(proj_data)

                dst_shape = proj_data['shape']
                dst_corner_ys = [crn[k]['y'][1][0] for k in crn.keys()]
                dst_corner_xs = [crn[k]['x'][1][0] for k in crn.keys()]
                y_pixel = abs(max(dst_corner_ys) - min(dst_corner_ys)) / dst_shape[0]
                x_pixel = abs(max(dst_corner_xs) - min(dst_corner_xs)) / dst_shape[1]
                dst_transform = (min(dst_corner_xs),
                                 x_pixel,
                                 0.0,
                                 max(dst_corner_ys),
                                 0.0,
                                 -y_pixel)

                new_bands = []
                for i in range(0, 2):
                    new_bands.append(numpy.empty(dst_shape, dtype=numpy.float32))

                self.output("Projecting", normal=True, arrow=True)
                proj_data["dst_transform"] = dst_transform
                self._warp(proj_data, bands, new_bands)

                for i in range(0, 2):
                    new_bands[i] = new_bands[i].astype(numpy.float32)

                output_band = numpy.true_divide((new_bands[1] - new_bands[0]), (new_bands[1] + new_bands[0]))

                output_file = '%s_NDVI.TIF' % (self.scene)
                output_file = join(self.dst_path, output_file)

                output = rasterio.open(output_file, 'w', driver='GTiff',
                                       width=dst_shape[1],
                                       height=dst_shape[0],
                                       count=1,
                                       dtype=numpy.uint8,
                                       nodata=0,
                                       transform=dst_transform,
                                       crs=self.dst_crs)

                output.write_band(1, img_as_ubyte(output_band))
                self.output("Writing to file", normal=True, color='green', indent=1)
                return output_file


if __name__ == '__main__':

    with timer():
        p = NDVI(sys.argv[1])

        print p.run()
