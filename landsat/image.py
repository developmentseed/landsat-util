# Pansharpened Image Process using Rasterio
# Landsat Util
# License: CC0 1.0 Universal

from __future__ import print_function, division, absolute_import

import os
import tarfile
import glob
from copy import copy
import subprocess
from shutil import copyfile
from os.path import join, isdir

import numpy
import rasterio
from rasterio.coords import disjoint_bounds
from rasterio.warp import reproject, RESAMPLING, transform, transform_bounds

from skimage import transform as sktransform
from skimage.util import img_as_ubyte
from skimage.exposure import rescale_intensity
from polyline.codec import PolylineCodec

from .mixins import VerbosityMixin
from .utils import get_file, check_create_folder, exit, adjust_bounding_box
from .decorators import rasterio_decorator


class FileDoesNotExist(Exception):
    """ Exception to be used when the file does not exist. """
    pass


class BoundsDoNotOverlap(Exception):
    """ Exception for when bounds do not overlap with the image """
    pass


class BaseProcess(VerbosityMixin):
    """
    Image procssing class

    To initiate the following parameters must be passed:

    :param path:
        Path of the image.
    :type path:
        String
    :param bands:
        The band sequence for the final image. Must be a python list. (optional)
    :type bands:
        List
    :param dst_path:
        Path to the folder where the image should be stored. (optional)
    :type dst_path:
        String
    :param verbose:
        Whether the output should be verbose. Default is False.
    :type verbose:
        boolean
    :param force_unzip:
        Whether to force unzip the tar file. Default is False
    :type force_unzip:
        boolean

    """

    def __init__(self, path, bands=None, dst_path=None, verbose=False, force_unzip=False, bounds=None):

        self.projection = {'init': 'epsg:3857'}
        self.dst_crs = {'init': u'epsg:3857'}
        self.scene = get_file(path).split('.')[0]
        self.bands = bands if isinstance(bands, list) else [4, 3, 2]
        self.clipped = False

        # Landsat source path
        self.src_path = path.replace(get_file(path), '')

        # Build destination folder if doesn't exist
        self.dst_path = dst_path if dst_path else os.getcwd()
        self.dst_path = check_create_folder(join(self.dst_path, self.scene))
        self.verbose = verbose

        # Path to the unzipped folder
        self.scene_path = join(self.src_path, self.scene)

        # Unzip files
        if self._check_if_zipped(path):
            self._unzip(join(self.src_path, get_file(path)), join(self.src_path, self.scene), self.scene, force_unzip)

        if (bounds):
            self.bounds = bounds
            self.scene_path = self.clip()
            self.clipped = True

        self.bands_path = []
        for band in self.bands:
            self.bands_path.append(join(self.scene_path, self._get_full_filename(band)))

    def _get_boundaries(self, src, shape):

        self.output("Getting boundaries", normal=True, arrow=True)
        output = {'ul': {'x': [0, 0], 'y': [0, 0]},  # ul: upper left
                  'ur': {'x': [0, 0], 'y': [0, 0]},  # ur: upper right
                  'll': {'x': [0, 0], 'y': [0, 0]},  # ll: lower left
                  'lr': {'x': [0, 0], 'y': [0, 0]}}  # lr: lower right

        output['ul']['x'][0] = src['affine'][2]
        output['ul']['y'][0] = src['affine'][5]
        output['ur']['x'][0] = output['ul']['x'][0] + self.pixel * src['shape'][1]
        output['ur']['y'][0] = output['ul']['y'][0]
        output['ll']['x'][0] = output['ul']['x'][0]
        output['ll']['y'][0] = output['ul']['y'][0] - self.pixel * src['shape'][0]
        output['lr']['x'][0] = output['ul']['x'][0] + self.pixel * src['shape'][1]
        output['lr']['y'][0] = output['ul']['y'][0] - self.pixel * src['shape'][0]

        output['ul']['x'][1], output['ul']['y'][1] = transform(src['crs'], self.projection,
                                                               [output['ul']['x'][0]],
                                                               [output['ul']['y'][0]])

        output['ur']['x'][1], output['ur']['y'][1] = transform(src['crs'], self.projection,
                                                               [output['ur']['x'][0]],
                                                               [output['ur']['y'][0]])

        output['ll']['x'][1], output['ll']['y'][1] = transform(src['crs'], self.projection,
                                                               [output['ll']['x'][0]],
                                                               [output['ll']['y'][0]])

        output['lr']['x'][1], output['lr']['y'][1] = transform(src['crs'], self.projection,
                                                               [output['lr']['x'][0]],
                                                               [output['lr']['y'][0]])

        dst_corner_ys = [output[k]['y'][1][0] for k in output.keys()]
        dst_corner_xs = [output[k]['x'][1][0] for k in output.keys()]
        y_pixel = abs(max(dst_corner_ys) - min(dst_corner_ys)) / shape[0]
        x_pixel = abs(max(dst_corner_xs) - min(dst_corner_xs)) / shape[1]

        return (min(dst_corner_xs), x_pixel, 0.0, max(dst_corner_ys), 0.0, -y_pixel)

    def _read_bands(self):
        """ Reads a band with rasterio """
        bands = []

        try:
            for i, band in enumerate(self.bands):
                bands.append(rasterio.open(self.bands_path[i]).read_band(1))
        except IOError as e:
            exit(e.message, 1)

        return bands

    def _warp(self, proj_data, bands, new_bands):
        self.output("Projecting", normal=True, arrow=True)
        for i, band in enumerate(bands):
            self.output("band %s" % self.bands[i], normal=True, color='green', indent=1)
            reproject(band, new_bands[i], src_transform=proj_data['transform'], src_crs=proj_data['crs'],
                      dst_transform=proj_data['dst_transform'], dst_crs=self.dst_crs, resampling=RESAMPLING.nearest,
                      num_threads=2)

    def _unzip(self, src, dst, scene, force_unzip=False):
        """ Unzip tar files """
        self.output("Unzipping %s - It might take some time" % scene, normal=True, arrow=True)

        try:
            # check if file is already unzipped, skip
            if isdir(dst) and not force_unzip:
                self.output('%s is already unzipped.' % scene, normal=True, color='green', indent=1)
                return
            else:
                tar = tarfile.open(src, 'r')
                tar.extractall(path=dst)
                tar.close()
        except tarfile.ReadError:
            check_create_folder(dst)
            subprocess.check_call(['tar', '-xf', src, '-C', dst])

    def _get_full_filename(self, band):

        base_file = '%s_B%s.*' % (self.scene, band)

        try:
            return glob.glob(join(self.scene_path, base_file))[0].split('/')[-1]
        except IndexError:
            raise FileDoesNotExist('%s does not exist' % '%s_B%s.*' % (self.scene, band))

    def _check_if_zipped(self, path):
        """ Checks if the filename shows a tar/zip file """

        filename = get_file(path).split('.')

        if filename[-1] in ['bz', 'bz2', 'gz']:
            return True

        return False

    def _read_metadata(self):
        output = {}
        try:
            with open(self.scene_path + '/' + self.scene + '_MTL.txt', 'rU') as mtl:
                lines = mtl.readlines()
                for line in lines:
                    if 'REFLECTANCE_ADD_BAND_3' in line:
                        output['REFLECTANCE_ADD_BAND_3'] = float(line.replace('REFLECTANCE_ADD_BAND_3 = ', ''))

                    if 'REFLECTANCE_MULT_BAND_3' in line:
                        output['REFLECTANCE_MULT_BAND_3'] = float(line.replace('REFLECTANCE_MULT_BAND_3 = ', ''))

                    if 'REFLECTANCE_ADD_BAND_4' in line:
                        output['REFLECTANCE_ADD_BAND_4'] = float(line.replace('REFLECTANCE_ADD_BAND_4 = ', ''))

                    if 'REFLECTANCE_MULT_BAND_4' in line:
                        output['REFLECTANCE_MULT_BAND_4'] = float(line.replace('REFLECTANCE_MULT_BAND_4 = ', ''))

                    if 'CLOUD_COVER' in line:
                        output['CLOUD_COVER'] = float(line.replace('CLOUD_COVER = ', ''))

                    return output
        except IOError:
            return output

    def _get_image_data(self):
        src = rasterio.open(self.bands_path[-1])

        # Get pixel size from source
        self.pixel = src.affine[0]

        # Only collect src data that is needed and delete the rest
        image_data = {
            'transform': src.transform,
            'crs': src.crs,
            'affine': src.affine,
            'shape': src.shape,
            'dst_transform': None
        }

        image_data['dst_transform'] = self._get_boundaries(image_data, image_data['shape'])

        return image_data

    def _generate_new_bands(self, shape):
        new_bands = []
        for i in range(0, 3):
            new_bands.append(numpy.empty(shape, dtype=numpy.uint16))

        return new_bands

    @rasterio_decorator
    def _write_to_file(self, new_bands, **kwargs):

        # Read coverage from QBA
        coverage = self._calculate_cloud_ice_perc()

        self.output("Final Steps", normal=True, arrow=True)

        suffix = 'bands_%s' % "".join(map(str, self.bands))

        output_file = join(self.dst_path, self._filename(suffix=suffix))

        output = rasterio.open(output_file, 'w', **kwargs)

        for i, band in enumerate(new_bands):
            # Color Correction
            band = self._color_correction(band, self.bands[i], 0, coverage)

            output.write_band(i + 1, img_as_ubyte(band))

            new_bands[i] = None
        self.output("Writing to file", normal=True, color='green', indent=1)

        return output_file

    def _color_correction(self, band, band_id, low, coverage):
        if self.bands == [4, 5]:
            return band
        else:
            self.output("Color correcting band %s" % band_id, normal=True, color='green', indent=1)
            p_low, cloud_cut_low = self._percent_cut(band, low, 100 - (coverage * 3 / 4))
            temp = numpy.zeros(numpy.shape(band), dtype=numpy.uint16)
            cloud_divide = 65000 - coverage * 100
            mask = numpy.logical_and(band < cloud_cut_low, band > 0)
            temp[mask] = rescale_intensity(band[mask], in_range=(p_low, cloud_cut_low), out_range=(256, cloud_divide))
            temp[band >= cloud_cut_low] = rescale_intensity(band[band >= cloud_cut_low],
                                                            out_range=(cloud_divide, 65535))
            return temp

    def _percent_cut(self, color, low, high):
        return numpy.percentile(color[numpy.logical_and(color > 0, color < 65535)], (low, high))

    def _calculate_cloud_ice_perc(self):
        """ Return the percentage of pixels that are either cloud or snow with
        high confidence (> 67%).
        """
        self.output('Calculating cloud and snow coverage from QA band', normal=True, arrow=True)
        a = rasterio.open(join(self.scene_path, self._get_full_filename('QA'))).read_band(1)

        cloud_high_conf = int('1100000000000000', 2)
        snow_high_conf = int('0000110000000000', 2)
        fill_pixels = int('0000000000000001', 2)
        cloud_mask = numpy.bitwise_and(a, cloud_high_conf) == cloud_high_conf
        snow_mask = numpy.bitwise_and(a, snow_high_conf) == snow_high_conf
        fill_mask = numpy.bitwise_and(a, fill_pixels) == fill_pixels

        perc = numpy.true_divide(numpy.sum(cloud_mask | snow_mask),
                                 a.size - numpy.sum(fill_mask)) * 100.0
        self.output('cloud/snow coverage: %s' % round(perc, 2), indent=1, normal=True, color='green')
        return perc

    def _filename(self, name=None, suffix=None, prefix=None):
        """ File name generator for processed images """

        filename = ''

        if prefix:
            filename += str(prefix) + '_'

        if name:
            filename += str(name)
        else:
            filename += str(self.scene)

        if suffix:
            filename += '_' + str(suffix)

        if self.clipped:
            bounds = [tuple(self.bounds[0:2]), tuple(self.bounds[2:4])]
            polyline = PolylineCodec().encode(bounds)
            filename += '_clipped_' + polyline

        filename += '.TIF'

        return filename

    @rasterio_decorator
    def clip(self):
        """ Clip images based on bounds provided
        Implementation is borrowed from
        https://github.com/brendan-ward/rasterio/blob/e3687ce0ccf8ad92844c16d913a6482d5142cf48/rasterio/rio/convert.py
        """

        self.output("Clipping", normal=True)

        # create new folder for clipped images
        path = check_create_folder(join(self.scene_path, 'clipped'))

        try:
            temp_bands = copy(self.bands)
            temp_bands.append('QA')
            for i, band in enumerate(temp_bands):
                band_name = self._get_full_filename(band)
                band_path = join(self.scene_path, band_name)

                self.output("Band %s" % band, normal=True, color='green', indent=1)
                with rasterio.open(band_path) as src:
                    bounds = transform_bounds(
                        {
                            'proj': 'longlat',
                            'ellps': 'WGS84',
                            'datum': 'WGS84',
                            'no_defs': True
                        },
                        src.crs,
                        *self.bounds
                    )

                    if disjoint_bounds(bounds, src.bounds):
                        bounds = adjust_bounding_box(src.bounds, bounds)

                    window = src.window(*bounds)

                    out_kwargs = src.meta.copy()
                    out_kwargs.update({
                        'driver': 'GTiff',
                        'height': window[0][1] - window[0][0],
                        'width': window[1][1] - window[1][0],
                        'transform': src.window_transform(window)
                    })

                    with rasterio.open(join(path, band_name), 'w', **out_kwargs) as out:
                        out.write(src.read(window=window))

            # Copy MTL to the clipped folder
            copyfile(join(self.scene_path, self.scene + '_MTL.txt'), join(path, self.scene + '_MTL.txt'))

            return path

        except IOError as e:
            exit(e.message, 1)


class Simple(BaseProcess):

    @rasterio_decorator
    def run(self):
        """ Executes the image processing.

        :returns:
            (String) the path to the processed image
        """

        self.output('Image processing started for bands %s' % '-'.join(map(str, self.bands)), normal=True, arrow=True)

        bands = self._read_bands()
        image_data = self._get_image_data()

        new_bands = self._generate_new_bands(image_data['shape'])

        self._warp(image_data, bands, new_bands)

        # Bands are no longer needed
        del bands

        rasterio_options = {
            'driver': 'GTiff',
            'width': image_data['shape'][1],
            'height': image_data['shape'][0],
            'count': 3,
            'dtype': numpy.uint8,
            'nodata': 0,
            'transform': image_data['dst_transform'],
            'photometric': 'RGB',
            'crs': self.dst_crs
        }

        return self._write_to_file(new_bands, **rasterio_options)


class PanSharpen(BaseProcess):

    def __init__(self, path, bands=None, **kwargs):
        if bands:
            bands.append(8)
        else:
            bands = [4, 3, 2, 8]

        self.band8 = bands.index(8)
        super(PanSharpen, self).__init__(path, bands, **kwargs)

    @rasterio_decorator
    def run(self):
        """ Executes the pansharpen image processing.
        :returns:
            (String) the path to the processed image
        """

        self.output('PanSharpened Image processing started for bands %s' % '-'.join(map(str, self.bands)),
                    normal=True, arrow=True)

        bands = self._read_bands()
        image_data = self._get_image_data()

        new_bands = self._generate_new_bands(image_data['shape'])

        bands[:3] = self._rescale(bands[:3])
        new_bands.append(numpy.empty(image_data['shape'], dtype=numpy.uint16))

        self._warp(image_data, bands, new_bands)

        # Bands are no longer needed
        del bands

        # Calculate pan band
        pan = self._pansize(new_bands)
        del self.bands[self.band8]
        del new_bands[self.band8]

        rasterio_options = {
            'driver': 'GTiff',
            'width': image_data['shape'][1],
            'height': image_data['shape'][0],
            'count': 3,
            'dtype': numpy.uint8,
            'nodata': 0,
            'transform': image_data['dst_transform'],
            'photometric': 'RGB',
            'crs': self.dst_crs
        }

        return self._write_to_file(new_bands, pan, **rasterio_options)

    @rasterio_decorator
    def _write_to_file(self, new_bands, pan, **kwargs):

        # Read coverage from QBA
        coverage = self._calculate_cloud_ice_perc()

        self.output("Final Steps", normal=True, arrow=True)

        suffix = 'bands_%s_pan' % "".join(map(str, self.bands))

        output_file = join(self.dst_path, self._filename(suffix=suffix))

        output = rasterio.open(output_file, 'w', **kwargs)

        for i, band in enumerate(new_bands):
            # Color Correction
            band = numpy.multiply(band, pan)
            band = self._color_correction(band, self.bands[i], 0, coverage)

            output.write_band(i + 1, img_as_ubyte(band))

            new_bands[i] = None

        self.output("Writing to file", normal=True, color='green', indent=1)

        return output_file

    def _pansize(self, bands):

        self.output('Calculating Pan Ratio', normal=True, arrow=True)

        m = numpy.add(bands[0], bands[1])
        m = numpy.add(m, bands[2])
        pan = numpy.multiply(numpy.nan_to_num(numpy.true_divide(1, m)), bands[self.band8])

        return pan

    def _rescale(self, bands):
        """ Rescale bands """
        self.output("Rescaling", normal=True, arrow=True)

        for key, band in enumerate(bands):
            self.output("band %s" % self.bands[key], normal=True, color='green', indent=1)
            bands[key] = sktransform.rescale(band, 2)
            bands[key] = (bands[key] * 65535).astype('uint16')

        return bands

if __name__ == '__main__':

    p = PanSharpen('/Users/ajdevseed/Desktop/LC81950282014159LGN00')

    p.run()
