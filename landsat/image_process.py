# Pansharpened Image Process using Rasterio
# Author: Marc Farra

import sys
from os.path import join, dirname
import tarfile
import numpy
import rasterio
from rasterio.warp import reproject, RESAMPLING, transform

from skimage import img_as_ubyte, exposure
from skimage import transform as sktransform

import settings
from general_helper import Verbosity


class Process(Verbosity):
    """
    Image procssing class
    """

    def __init__(self, scene, bands=[4, 3, 2], src_path=None, dst_path=None, zipped=None, verbose=False):
        """
        @params
        scene - the scene ID
        bands - The band sequence for the final image. Must be a python list
        src_path - The path to the source image bundle
        dst_path - The destination path
        zipped - Set to true if the scene is in zip format and requires unzipping
        verbose - Whether to show verbose output
        """

        self.projection = {'init': 'epsg:3857'}
        self.dst_crs = {'init': u'epsg:3857'}
        self.scene = scene
        self.bands = bands
        self.src_path = src_path if src_path else dirname(dirname(__file__))
        self.dst_path = dst_path if dst_path else settings.PROCESSED_IMAGE

        self.output_file = join(self.dst_path, 'landsat-pan.TIF')
        self.verbose = verbose

        self.scene_path = join(self.src_path, scene)

        self.bands_path = []
        for band in self.bands:
            self.bands_path.append(join(self.scene_path, '%s_B%s.TIF' % (self.scene, band)))

        # self.band8_path = join(self.scene_path, '%s_B8.TIF' % self.scene)

        if zipped:
            self._unzip(join(self.src_path, self.scene) + '.tar.bz', join(self.src_path, self.scene), self.scene)

    def pansherpen(self):

        self.output("* Image processing started", normal=True)

        with rasterio.drivers():
            bands = []

            # Add bands 8 for pansharpenning
            self.bands.append(8)

            bands_path = []
            for band in self.bands:
                bands_path.append(join(self.scene_path, '%s_B%s.TIF' % (self.scene, band)))

            for i, band in enumerate(self.bands):
                bands.append(self._read_band(bands_path[i]))

            # open band 8 separately
            src = rasterio.open(bands_path[3])

            crn = self._get_bounderies(src)

            dst_shape = (int((crn['lr']['x'][1][0] - crn['ul']['x'][1][0])/15),
                         int((crn['lr']['y'][1][0] - crn['ul']['y'][1][0])/15))

            dst_transform = (crn['ul']['x'][1][0], 15, 0.0, crn['ul']['y'][1][0], 0.0, -15)

            r = numpy.empty(dst_shape, dtype=numpy.uint16)
            g = numpy.empty(dst_shape, dtype=numpy.uint16)
            b = numpy.empty(dst_shape, dtype=numpy.uint16)
            b8 = numpy.empty(dst_shape, dtype=numpy.uint16)

            bands[:3] = self._rescale(bands[:3])

            new_bands = [r, g, b, b8]

            self.output("Projecting", normal=True, arrow=True)
            for i, band in enumerate(bands):
                self.output("Projecting band %s" % (i + 1), normal=True, color='green', indent=1)
                reproject(band, new_bands[i], src_transform=src.transform, src_crs=src.crs,
                          dst_transform=dst_transform, dst_crs=self.dst_crs, resampling=RESAMPLING.nearest)

            print numpy.sum(b8)

            self.output("Pansharpening", normal=True, arrow=True)
            # Pan sharpening
            m = r + b + g
            m = m + 0.1

            self.output("calculating pan ratio", normal=True, color='green', indent=1)
            pan = 1/m * b8
            self.output("computing bands", normal=True, color='green', indent=1)

            r = r * pan
            b = b * pan
            g = g * pan

            r = r.astype(numpy.uint16)
            g = g.astype(numpy.uint16)
            b = b.astype(numpy.uint16)

            self.output("Color correcting", normal=True, arrow=True)
            p2r, p98r = self._percent_cut(r)
            p2g, p98g = self._percent_cut(g)
            p2b, p98b = self._percent_cut(b)
            r = exposure.rescale_intensity(r, in_range=(p2r, p98r))
            g = exposure.rescale_intensity(g, in_range=(p2g, p98g))
            b = exposure.rescale_intensity(b, in_range=(p2b, p98b))

            # Gamma correction
            r = exposure.adjust_gamma(r, 1.1)
            b = exposure.adjust_gamma(b, 0.9)

            self.output("Writing output", normal=True, arrow=True)
            output = rasterio.open(self.output_file, 'w', driver='GTiff',
                                   width=dst_shape[1], height=dst_shape[0],
                                   count=3, dtype=numpy.uint8,
                                   nodata=0, transform=dst_transform, photometric='RGB',
                                   crs=self.dst_crs)

            new_bands = [r, g, b]

            for i, band in enumerate(new_bands):
                output.write_band(i+1, img_as_ubyte(band))

            return self.output_file

    def _percent_cut(self, color):
        return numpy.percentile(color[numpy.logical_and(color > 0, color < 65535)], (2, 98))

    def _unzip(self, src, dst, scene):
        """ Unzip tar files """
        self.output("Unzipping %s - It might take some time" % scene, normal=True, arrow=True)
        tar = tarfile.open(src)
        tar.extractall(path=dst)
        tar.close()

    def _read_band(self, band_path):
        """ Reads a band with rasterio """
        return rasterio.open(band_path).read_band(1)

    def _rescale(self, bands):
        """ Rescale bands """
        self.output("Rescaling", normal=True, arrow=True)

        for key, band in enumerate(bands):
            self.output("Rescaling band %s" % (key + 1), normal=True, color='green', indent=1)
            bands[key] = sktransform.rescale(band, 2)
            bands[key] = (bands[key] * 65535).astype('uint16')

        return bands

    def _get_projection(self, src):
        return {'init': unicode.encode(src.crs['init'])}

    def _get_bounderies(self, src):

        self.output("Getting bounderies", normal=True, arrow=True)
        output = {'ul': {'x': [0, 0], 'y': [0, 0]},  # ul: upper left
                  'lr': {'x': [0, 0], 'y': [0, 0]}}  # lr: lower right

        output['ul']['x'][0] = src.affine[2]
        output['ul']['y'][0] = src.affine[5]
        output['ul']['x'][1], output['ul']['y'][1] = transform(src.crs, self.projection,
                                                               [output['ul']['x'][0]],
                                                               [output['ul']['y'][0]])
        output['lr']['x'][0] = output['ul']['x'][0] + 15 * src.shape[0]
        output['lr']['y'][0] = output['ul']['y'][0] + 15 * src.shape[1]
        output['lr']['x'][1], output['lr']['y'][1] = transform(src.crs, self.projection,
                                                               [output['lr']['x'][0]],
                                                               [output['lr']['y'][0]])

        return output


if __name__ == '__main__':

    p = Process(sys.argv[1],
                src_path=sys.argv[2],
                dst_path=sys.argv[2])

    print p.pansherpen()

