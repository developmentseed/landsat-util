# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributor: scisco, KAPPS-, willemarcel
#
# License: CC0 1.0 Universal

import os
import subprocess
import errno
import shutil
import tarfile
from tempfile import mkdtemp
import struct

import numpy
from osgeo import gdal
try:
    import cv2
except ImportError:
    pass

import settings
from general_helper import check_create_folder, get_file


def gdalwarp(src, dst, t_srs=None):
    """ A subporcess wrapper for gdalwarp """
    argv = ['gdalwarp']
    if t_srs:
        argv.append('-t_srs')
        argv.append(t_srs)
    argv.append('-overwrite')
    argv.append(src)
    argv.append(dst)

    return subprocess.check_call(argv)


def gdal_translate(src, dst, **kwargs):
    """ A subprocess wrapper for gdal_translate """
    argv = ['gdal_translate']

    for key, value in kwargs.iteritems():
        argv.append('-%s' % key)
        if isinstance(value, list):
            for item in value:
                argv.append(str(item))
        else:
            argv.append(str(value))

    argv.append(src)
    argv.append(dst)

    return subprocess.check_call(argv)


class Process(object):

    """ Full image processing class

    Steps needed for a full process
    1) _wrap()
    2) _scale_pan()
    3) _combine_rgb()
    4) _image_correction()
    5) _final_conversions()
    """

    def __init__(self, zip_image, bands=[7, 5, 4, 3, 2], path=None):
        """ Initating the Process class

        Arguments:
            image - the string containing the name of the image folder e.g. LC80030032014158LGN00
            bands - a list of desired bands. Default is for True color
            path - Path to where the image folder is located

        """
        self.image = get_file(zip_image).split('.')[0]
        self.destination = settings.PROCESSED_IMAGE
        self.bands = bands

        self.btm_prct = 2
        self.top_prct = 2

        if path:
            self.path = path

        self.temp = mkdtemp()
        self.src_image_path = self.temp + '/' + self.image
        self.warp_path = self.temp + '/' + self.image + '/warp'
        self.scaled_path = self.temp + '/' + self.image + '/scaled'
        self.final_path = self.temp + '/' + self.image + '/final'
        self.delivery_path = self.destination + '/' + self.image

        check_create_folder(self.src_image_path)
        check_create_folder(self.warp_path)
        check_create_folder(self.scaled_path)
        check_create_folder(self.final_path)
        check_create_folder(self.delivery_path)

        self._unzip(zip_image, self.src_image_path)

    def full(self, args):
        """ Conducts the full image processing """
        self._warp()
        self._scale_pan()
        self._combine_rgb()
        self._image_correction()
        self._final_conversions()
        final_image = self._create_mask()
        shutil.copy(final_image, self.delivery_path)
        if args.ndvi:
            if args.noclouds:
                ndvi_image = self._ndvi(noclouds=True)
            else:
                ndvi_image = self._ndvi()
            shutil.copy(ndvi_image, self.delivery_path)
        if args.swirnir:
            self._swirnir(pansharp=False)
        self._cleanup()

        return

    def full_with_pansharpening(self, args):
        self._warp()
        self._scale_pan()
        self._combine_rgb()
        self._image_correction()
        self._final_conversions()
        final_image = self._create_mask()
        shutil.copy(final_image, self.delivery_path)
        if args.ndvi:
            if args.noclouds:
                ndvi_image = self._ndvi(noclouds=True)
            else:
                ndvi_image = self._ndvi()
            shutil.copy(ndvi_image, self.delivery_path)
        if args.swirnir:
            self._swirnir(pansharp=True)
        shutil.copy(self._pansharpen(), self.delivery_path)
        self._cleanup()

        return

    def _cleanup(self):
        """ Remove temp folder """
        try:
            shutil.rmtree(self.temp)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

    def _pansharpen(self, file_name='final-color.TIF'):
        file_name = file_name.replace('.TIF', '')
        compfile = '%s/comp-%s.TIF' % (self.final_path, file_name)

        shutil.copy('%s/%s_B4.tfw' % (self.warp_path, self.image),
                    '%s/comp-%s.tfw' % (self.final_path, file_name))

        argv = ['gdal_edit.py', '-a_srs', 'EPSG:3857',
                compfile]

        subprocess.check_call(argv)

        argv = ['otbcli_BundleToPerfectSensor',
                # '-ram', '6500',
                '-inp', '%s/%s_B8.TIF' % (self.warp_path, self.image),
                '-inxs', compfile,
                '-out', '%s/pan.TIF' % self.final_path,
                'uint16']

        subprocess.check_call(argv)

        for i in range(1, 4):
            gdal_translate('%s/pan.TIF' % self.final_path,
                           '%s/pan-%s.TIF' % (self.final_path, i),
                           b=i)

        argv = ['convert', '-combine']

        for i in range(1, 4):
            argv.append('%s/pan-%s.TIF' % (self.final_path, i))

        argv.append('%s/pan.TIF' % self.final_path)

        subprocess.check_call(argv)

        argv = ['convert', '-depth', '8',
                '%s/pan.TIF' % self.final_path,
                '%s/%s-pan.TIF' % (self.final_path, file_name)]

        subprocess.check_call(argv)

        argv = ['listgeo', '-tfw',
                '%s/%s_B8.TIF' % (self.warp_path, self.image)]

        subprocess.check_call(argv)

        shutil.copy('%s/%s_B8.tfw' % (self.warp_path, self.image),
                    '%s/%s-pan.tfw' % (self.final_path, file_name))

        argv = ['gdal_edit.py', '-a_srs', 'EPSG:3857',
                '%s/final-pan.TIF' % self.final_path]

        subprocess.check_call(argv)

        return '%s/%s-pan.TIF' % (self.final_path, file_name)

    def _create_mask(self, file_name='final-color.TIF'):
        file_name = file_name.replace('.TIF', '')

        argv = ['gdal_calc.py',
                '-A', '%s/%s_B2.TIF' % (self.warp_path, self.image),
                '--outfile=%s/band-mask.TIF' % self.final_path,
                '--calc=1*(A>0)',
                '--type=UInt16']

        subprocess.check_call(argv)

        finalfile = '%s/%s.TIF' % (self.final_path, file_name)

        for i in range(1, 4):
            gdal_translate(finalfile,
                           '%s/band-%s.TIF' % (self.final_path, i),
                           b=i)

        for i in range(1, 4):
            argv = ['gdal_calc.py',
                    '-A', '%s/band-%s.TIF' % (self.final_path, i),
                    '-B', '%s/band-mask.TIF' % (self.final_path),
                    '--outfile=%s/maksed-final-%s.TIF' % (self.final_path, i),
                    '--calc=A*B',
                    '--type=UInt16']

            subprocess.check_call(argv)

        argv = ['convert', '-combine']

        for i in range(1, 4):
            argv.append('%s/maksed-final-%s.TIF' % (self.final_path, i))

        compfile = '%s/comp-%s.TIF' % (self.final_path, file_name)
        argv.append(compfile)

        subprocess.check_call(argv)

        argv = ['convert', '-depth', '8',
                compfile,
                '%s/final.TIF' % self.final_path]

        subprocess.check_call(argv)

        argv = ['listgeo', '-tfw',
                '%s/%s_B4.TIF' % (self.warp_path, self.image)]

        subprocess.check_call(argv)

        shutil.copy('%s/%s_B4.tfw' % (self.warp_path, self.image),
                    '%s/%s.tfw' % (self.final_path, file_name))

        argv = ['gdal_edit.py', '-a_srs', 'EPSG:3857',
                '%s/%s.TIF' % (self.final_path, file_name)]

        subprocess.check_call(argv)

        return '%s/%s.TIF' % (self.final_path, file_name)

    def _final_conversions(self):
        """ Final color conversions. Return final image temp path """
        print 'Convertin image tweaks'

        # First conversion
        argv = ['convert',
                '-channel', 'B', '-gamma', '0.98',
                '-channel', 'R', '-gamma', '1.03',
                '-channel', 'RGB', '-sigmoidal-contrast', '50x15%',
                '%s/rgb-null.TIF' % self.final_path,
                '%s/rgb-sig.TIF' % self.final_path]

        subprocess.check_call(argv)

        # Second conversion
        argv = ['convert',
                '-channel', 'B', '-gamma', '0.98',
                '-channel', 'R', '-gamma', '1.03',
                '%s/rgb-scaled.TIF' % self.final_path,
                '%s/rgb-scaled-cc.TIF' % self.final_path]

        subprocess.check_call(argv)

        print 'Convert: averaging'

        # Fourth conversion
        argv = ['convert',
                '%s/rgb-sig.TIF' % self.final_path,
                '%s/rgb-scaled-cc.TIF' % self.final_path,
                '-evaluate-sequence', 'mean',
                '%s/final-col.TIF' % self.final_path]

        subprocess.check_call(argv)

        print 'Convert: Gamma'

        # Fifth conversion
        argv = ['convert',
                '-gamma', '1.35',
                '%s/final-col.TIF' % self.final_path,
                '%s/final-color.TIF' % self.final_path]

        subprocess.check_call(argv)

    def _image_correction(self):
        try:
            corrected_list = []

            band_correction = [[2, 0.97], [4, 1.04]]

            for band in [4, 3, 2]:

                print 'Starting the image processing'

                file_path = ('%s/%s_B%s.TIF' % (self.warp_path,
                                                self.image, band))

                img = cv2.imread(file_path, 0)    #-1 if the next package is released and includes (https://github.com/Itseez/opencv/pull/3033)

                # Gamma Correction
                for c in band_correction:
                    if c[0] == band:
                        img = img ** c[1]

                # adding color corrected band back to list
                corrected_list.append(img.astype(numpy.uint8))

            # combining bands in list into a bgr img (opencv format for true color)
            b, g, r = corrected_list[2], corrected_list[1], corrected_list[0]

            img_comp = cv2.merge((b, g, r))

            # converting bgr to ycrcb
            imgy = cv2.cvtColor(img_comp, cv2.COLOR_BGR2YCR_CB)

            # extracting y
            y, cr, cb = cv2.split(imgy)

            # equalizing y with CLAHE
            clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(950, 950))
            y = clahe.apply(y)

            # merging equalized y with cr and cb
            imgy = cv2.merge((y, cr, cb))

            # converting ycrcb back to bgr
            img = cv2.cvtColor(imgy, cv2.COLOR_YCR_CB2BGR)

            # writing final equalized file
            cv2.imwrite('%s/eq-hist.tif' % self.final_path, img)
        except NameError, e:
            print e.args[0]
            print "Skipping Image Correction using OpenCV"

    def _combine_rgb(self):
        argv = ['convert', '-identify', '-combine']

        for band in [4, 3, 2]:
            argv.append('%s/%s_B%s.TIF' % (self.warp_path, self.image, band))

        argv.append('%s/rgb-null.TIF' % self.final_path)

        subprocess.check_call(argv)

        argv = ['convert', '-identify', '-combine']

        for band in [4, 3, 2]:
            argv.append('%s/%s_B%s.TIF' % (self.scaled_path, self.image, band))

        argv.append('%s/rgb-scaled.TIF' % self.final_path)

        subprocess.check_call(argv)

    def _scale_pan(self):
        """ scaling pan to min max with 2 percent cut """

        min_max = self._calculate_min_max()

        # min_max = [6247, 32888]

        min_max.extend([1, 255])

        for band in self.bands:

            print 'scaling pan to min max with 2%% cut for band %s' % band

            gdal_translate('%s/%s_B%s.TIF' % (self.warp_path,
                                              self.image, band),
                           '%s/%s_B%s.TIF' % (self.scaled_path,
                                              self.image, band),
                           ot='byte', scale=min_max
                           )

    def _calculate_min_max(self):
        """ Calculate Min/Max values with 2 percent cut """

        min_max_list = []

        for band in self.bands:

            file_path = ('%s/%s_B%s.TIF' % (self.warp_path,
                                            self.image, band))

            if os.path.exists(file_path):
                print ('Starting the Min/Max process with designated -percent '
                       'cut- for band %s of %s' % (band, self.image))
                print '...'

                # Open images in the warp folder
                ds = gdal.Open(file_path)

                # converting raster to numpy array
                values = numpy.array(ds.GetRasterBand(1).ReadAsArray())
                to_list = values.tolist()

                full_list = [item for sublist in to_list for item in sublist]

                # removing zeros
                value_list = filter(lambda x: x != 0, full_list)
                list_len = len(value_list)

                value_list.sort()

                # determining number of integers to cut from bottom of list
                cut_value_bottom = int(float(self.btm_prct) /
                                       float(100) * float(list_len))

                # determining number of integers to cut from top of list
                cut_value_top = int(float(self.top_prct) /
                                    float(100) * float(list_len))

                # establishing new min and max with percent cut
                cut_list = value_list[
                    (cut_value_bottom + 1):(list_len - cut_value_top)]

                # adding min and max with percent cut values to list
                min_max_list.extend([cut_list[0], cut_list[-1]])

                print 'Finished processing band %s of %s' % (band, self.image)

        return [min(min_max_list), max(min_max_list)]

    def _warp(self):
        """ Warping the images on provided bands + band 8 """

        # Adding band 8 to the band list
        new_bands = list(self.bands)
        new_bands.append(8)

        # Warping
        for band in new_bands:
            gdalwarp('%s/%s_B%s.TIF' % (self.src_image_path, self.image, band),
                     '%s/%s_B%s.TIF' % (self.warp_path, self.image, band),
                     t_srs='EPSG:3857')

    def _swirnir(self, pansharp):
        print 'Processing SWIR-NIR'
        argv = ['convert', '-identify', '-combine']

        for band in [7, 5, 3]:
            argv.append('%s/%s_B%s.TIF' % (self.warp_path, self.image, band))

        argv.append('%s/753-null.TIF' % self.final_path)

        subprocess.check_call(argv)

        argv = ['convert',
                '-channel', 'RGB', '-sigmoidal-contrast', '5x15%',
                '-channel', 'R', '-brightness-contrast', '30x80%',
                '-channel', 'G', '-brightness-contrast', '5x30%',
                '-channel', 'B', '-brightness-contrast', '35x30%',
                '%s/753-null.TIF' % self.final_path,
                '%s/final-753.TIF' % self.final_path]

        subprocess.check_call(argv)

        final_image = self._create_mask('final-753.TIF')

        shutil.copy(final_image, self.delivery_path)

        print 'SWIR-NIR Completed'
       
    def _ndvi(self, noclouds=False):
        """ Generate a NDVI image. If noclouds=True, the area of clouds and
        cirrus will be removed from the image and the NDVI value will be set
        to zero in this area. """

        b4 = gdal.Open('%s/%s_B4.TIF' % (self.src_image_path, self.image),
            gdal.GA_ReadOnly)
        b5 = gdal.Open('%s/%s_B5.TIF' % (self.src_image_path, self.image),
            gdal.GA_ReadOnly)
        bqa = gdal.Open('%s/%s_BQA.TIF' % (self.src_image_path, self.image),
            gdal.GA_ReadOnly)

        red_band = b4.GetRasterBand(1)
        nir_band = b5.GetRasterBand(1)
        bqa_band = bqa.GetRasterBand(1)
        numLines = red_band.YSize

        cloud_values = [61440, 59424, 57344, 56320, 53248, 52256, 52224, 49184,
            49152, 48128, 45056, 43040, 39936, 36896, 36864, 32768, 31744, 28672]

        outputFile = '%s/final-ndvi.TIF' % (self.final_path)
        driver = b4.GetDriver()
        outDataset = driver.Create(outputFile, b4.RasterXSize, b4.RasterYSize,
            1, gdal.GDT_Float32)
        outDataset.SetGeoTransform(b4.GetGeoTransform())
        outDataset.SetProjection(b4.GetProjection())

        for line in range(numLines):
            outputLine = ''
            red_scanline = red_band.ReadRaster(0, line, red_band.XSize, 1,
                red_band.XSize, 1, gdal.GDT_Float32)
            red_tuple = struct.unpack('f' * red_band.XSize, red_scanline)

            nir_scanline = nir_band.ReadRaster(0, line, nir_band.XSize, 1,
                nir_band.XSize, 1, gdal.GDT_Float32)
            nir_tuple = struct.unpack('f' * nir_band.XSize, nir_scanline)

            bqa_scanline = bqa_band.ReadRaster(0, line, bqa_band.XSize, 1,
                bqa_band.XSize, 1, gdal.GDT_Float32)
            bqa_tuple = struct.unpack('f' * bqa_band.XSize, bqa_scanline)

            for i in range(len(red_tuple)):
                if bqa_tuple[i] in cloud_values and noclouds:
                    ndvi = 0
                else:
                    ndvi_lower = (nir_tuple[i] + red_tuple[i])
                    ndvi_upper = (nir_tuple[i] - red_tuple[i])
                    ndvi = 0
                    if ndvi_lower == 0:
                        ndvi = 0
                    else:
                        ndvi = ndvi_upper / ndvi_lower

                outputLine = outputLine + struct.pack('f', ndvi)

            outDataset.GetRasterBand(1).WriteRaster(0, line, red_band.XSize, 1,
                outputLine, buf_xsize=red_band.XSize, buf_ysize=1,
                buf_type=gdal.GDT_Float32)
            del outputLine

        print 'NDVI Created'
        return outputFile

    def _unzip(self, src, dst):
        print "Unzipping %s - It might take some time" % self.image
        tar = tarfile.open(src)
        tar.extractall(path=dst)
        tar.close()

