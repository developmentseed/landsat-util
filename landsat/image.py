# Pansharpened Image Process using Rasterio
# Landsat Util
# License: CC0 1.0 Universal

import os
from os.path import join, isdir
import tarfile
import glob
import subprocess

import numpy
import rasterio
from rasterio.warp import reproject, RESAMPLING, transform

from skimage import transform as sktransform
from skimage.util import img_as_ubyte
from skimage.exposure import rescale_intensity

from mixins import VerbosityMixin
from utils import get_file, check_create_folder, exit
from decorators import rasterio_decorator


class FileDoesNotExist(Exception):
    """ Exception to be used when the file does not exist. """
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

    def __init__(self, path, bands=None, dst_path=None, verbose=False, force_unzip=False):

        self.projection = {'init': 'epsg:3857'}
        self.dst_crs = {'init': u'epsg:3857'}
        self.scene = get_file(path).split('.')[0]
        self.bands = bands if isinstance(bands, list) else [4, 3, 2]

        # Landsat source path
        self.src_path = path.replace(get_file(path), '')

        # Build destination folder if doesn't exist
        self.dst_path = dst_path if dst_path else os.getcwd()
        self.dst_path = check_create_folder(join(self.dst_path, self.scene))
        self.verbose = verbose

        # Path to the unzipped folder
        self.scene_path = join(self.src_path, self.scene)

        if self._check_if_zipped(path):
            self._unzip(join(self.src_path, get_file(path)), join(self.src_path, self.scene), self.scene, force_unzip)

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
                      dst_transform=proj_data['dst_transform'], dst_crs=self.dst_crs, resampling=RESAMPLING.nearest)

    def _unzip(self, src, dst, scene, force_unzip=False):
        """ Unzip tar files """
        self.output("Unzipping %s - It might take some time" % scene, normal=True, arrow=True)

        try:
            # check if file is already unzipped, skip
            if isdir(dst) and not force_unzip:
                self.output("%s is already unzipped." % scene, normal=True, arrow=True)
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

        if filename[-1] in ['bz', 'bz2']:
            return True

        return False

    def _read_cloud_cover(self):
        try:
            with open(self.scene_path + '/' + self.scene + '_MTL.txt', 'rU') as mtl:
                lines = mtl.readlines()
                for line in lines:
                    if 'CLOUD_COVER' in line:
                        return float(line.replace('CLOUD_COVER = ', ''))
        except IOError:
            return 0

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
    def _write_to_file(self, new_bands, suffix=None, **kwargs):

        # Read cloud coverage from mtl file
        cloud_cover = self._read_cloud_cover()

        self.output("Final Steps", normal=True, arrow=True)

        output_file = '%s_bands_%s' % (self.scene, "".join(map(str, self.bands)))

        if suffix:
            output_file += suffix

        output_file += '.TIF'
        output_file = join(self.dst_path, output_file)

        output = rasterio.open(output_file, 'w', **kwargs)

        for i, band in enumerate(new_bands):
            # Color Correction
            band = self._color_correction(band, self.bands[i], 0, cloud_cover)

            output.write_band(i+1, img_as_ubyte(band))

            new_bands[i] = None
        self.output("Writing to file", normal=True, color='green', indent=1)

        return output_file

    def _color_correction(self, band, band_id, low, cloud_cover):
        band = band.astype(numpy.uint16)

        self.output("Color correcting band %s" % band_id, normal=True, color='green', indent=1)
        p_low, cloud_cut_low = self._percent_cut(band, low, 100 - (cloud_cover * 3 / 4))
        temp = numpy.zeros(numpy.shape(band), dtype=numpy.uint16)
        cloud_divide = 65000 - cloud_cover * 100
        mask = numpy.logical_and(band < cloud_cut_low, band > 0)
        temp[mask] = rescale_intensity(band[mask], in_range=(p_low, cloud_cut_low), out_range=(256, cloud_divide))
        temp[band >= cloud_cut_low] = rescale_intensity(band[band >= cloud_cut_low], out_range=(cloud_divide, 65535))
        return temp

    def _percent_cut(self, color, low, high):
        return numpy.percentile(color[numpy.logical_and(color > 0, color < 65535)], (low, high))


class Simple(BaseProcess):

    @rasterio_decorator
    def run(self):
        """ Executes the image processing.

        :returns:
            (String) the path to the processed image
        """

        self.output("* Image processing started for bands %s" % "-".join(map(str, self.bands)), normal=True)

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

    def __init__(self, path, bands=None, dst_path=None, verbose=False, force_unzip=False):
        if bands:
            bands.append(8)
        else:
            bands = [4, 3, 2, 8]
        super(PanSharpen, self).__init__(path, bands, dst_path, verbose, force_unzip)

    @rasterio_decorator
    def run(self):
        """ Executes the pansharpen image processing.
        :returns:
            (String) the path to the processed image
        """

        self.output("* PanSharpened Image processing started for bands %s" % "-".join(map(str, self.bands)), normal=True)

        bands = self._read_bands()
        image_data = self._get_image_data()

        new_bands = self._generate_new_bands(image_data['shape'])

        bands[:3] = self._rescale(bands[:3])
        new_bands.append(numpy.empty(image_data['shape'], dtype=numpy.uint16))

        self._warp(image_data, bands, new_bands)

        # Bands are no longer needed
        del bands

        new_bands = self._pansharpenning(new_bands)
        del self.bands[3]

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

        return self._write_to_file(new_bands, '_pan', **rasterio_options)

    def _pansharpenning(self, bands):

        self.output("Pansharpening", normal=True, arrow=True)
        # Pan sharpening
        m = sum(bands[:3])
        m = m + 0.1

        self.output("calculating pan ratio", normal=True, color='green', indent=1)
        pan = 1/m * bands[-1]

        del m
        del bands[3]
        self.output("computing bands", normal=True, color='green', indent=1)

        for i, band in enumerate(bands):
            bands[i] = band * pan

        del pan

        return bands

    def _rescale(self, bands):
        """ Rescale bands """
        self.output("Rescaling", normal=True, arrow=True)

        for key, band in enumerate(bands):
            self.output("band %s" % self.bands[key], normal=True, color='green', indent=1)
            bands[key] = sktransform.rescale(band, 2)
            bands[key] = (bands[key] * 65535).astype('uint16')

        return bands
