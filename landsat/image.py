# Pansharpened Image Process using Rasterio
# Landsat Util
# License: CC0 1.0 Universal

import warnings
import sys
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

import settings
from mixins import VerbosityMixin
from utils import get_file, timer, check_create_folder, exit

#for color
import matplotlib.pylab as pyplot


class FileDoesNotExist(Exception):
    """ Exception to be used when the file does not exist. """
    pass


class Process(VerbosityMixin):
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

        # Build destination folder if doesn't exits
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

    def run_rgb(self, pansharpen=True):
        """ Executes the image processing.

        :param pansharpen:
            Whether the process should also run pansharpenning. Default is True
        :type pansharpen:
            boolean

        :returns:
            (String) the path to the processed image
        """

        self.output("* Image processing started for bands %s" % "-".join(map(str, self.bands)), normal=True)

        # Read cloud coverage from mtl file
        cloud_cover = 0
        try:
            with open(self.scene_path + '/' + self.scene + '_MTL.txt', 'rU') as mtl:
                lines = mtl.readlines()
                for line in lines:
                    if 'CLOUD_COVER' in line:
                        cloud_cover = float(line.replace('CLOUD_COVER = ', ''))
                        break
        except IOError:
            pass

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with rasterio.drivers():
                bands = []

                # Add band 8 for pansharpenning
                if pansharpen:
                    self.bands.append(8)

                bands_path = []

                for band in self.bands:
                    bands_path.append(join(self.scene_path, self._get_full_filename(band)))

                try:
                    for i, band in enumerate(self.bands):
                        bands.append(self._read_band(bands_path[i]))
                except IOError as e:
                    exit(e.message, 1)

                src = rasterio.open(bands_path[-1])

                # Get pixel size from source
                self.pixel = src.affine[0]

                # Only collect src data that is needed and delete the rest
                src_data = {
                    'transform': src.transform,
                    'crs': src.crs,
                    'affine': src.affine,
                    'shape': src.shape
                }
                del src

                crn = self._get_boundaries(src_data)

                dst_shape = src_data['shape']
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
                # Delete crn since no longer needed
                del crn

                new_bands = []
                for i in range(0, 3):
                    new_bands.append(numpy.empty(dst_shape, dtype=numpy.uint16))

                if pansharpen:
                    bands[:3] = self._rescale(bands[:3])
                    new_bands.append(numpy.empty(dst_shape, dtype=numpy.uint16))

                self.output("Projecting", normal=True, arrow=True)
                for i, band in enumerate(bands):
                    self.output("band %s" % self.bands[i], normal=True, color='green', indent=1)
                    reproject(band, new_bands[i], src_transform=src_data['transform'], src_crs=src_data['crs'],
                              dst_transform=dst_transform, dst_crs=self.dst_crs, resampling=RESAMPLING.nearest)

                # Bands are no longer needed
                del bands

                if pansharpen:
                    new_bands = self._pansharpenning(new_bands)
                    del self.bands[3]

                self.output("Final Steps", normal=True, arrow=True)

                output_file = '%s_bands_%s' % (self.scene, "".join(map(str, self.bands)))

                if pansharpen:
                    output_file += '_pan'

                output_file += '.TIF'
                output_file = join(self.dst_path, output_file)

                output = rasterio.open(output_file, 'w', driver='GTiff',
                                       width=dst_shape[1], height=dst_shape[0],
                                       count=3, dtype=numpy.uint8,
                                       nodata=0, transform=dst_transform, photometric='RGB',
                                       crs=self.dst_crs)

                for i, band in enumerate(new_bands):
                    # Color Correction
                    new_bands[i] = self._color_correction(band, self.bands[i], 0, cloud_cover)
                    
                self.output("Writing to file", normal=True, color='green', indent=1)
                for i, band in enumerate(new_bands):
                    output.write_band(i+1, img_as_ubyte(band))
                    new_bands[i] = None
                    
                return output_file

    def run_ndvi(self, mode='grey', cmask=False):
        """ Executes the image processing.

        :returns:
            (String) the path to the processed image
        """

        self.output("* Image processing started for NDVI", normal=True)

        # Read radiance conversion factors from mtl file
        try:
            with open(self.scene_path + '/' + self.scene + '_MTL.txt', 'rU') as mtl:
                lines = mtl.readlines()
                for line in lines:
                    if 'REFLECTANCE_ADD_BAND_3' in line:
                        add_B3 = float(line.replace('REFLECTANCE_ADD_BAND_3 = ', ''))
                    elif 'REFLECTANCE_MULT_BAND_3' in line:
                        mult_B3 = float(line.replace('REFLECTANCE_MULT_BAND_3 = ', ''))
                    elif 'REFLECTANCE_ADD_BAND_4' in line:
                        add_B4 = float(line.replace('REFLECTANCE_ADD_BAND_4 = ', ''))
                    elif 'REFLECTANCE_MULT_BAND_4' in line:
                        mult_B4 = float(line.replace('REFLECTANCE_MULT_BAND_4 = ', ''))
        except IOError:
            pass

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with rasterio.drivers():
                bands = []

                bands_path = []
                
                if cmask:
                    self.bands.append('QA')
                    
                for band in self.bands:
                    bands_path.append(join(self.scene_path, self._get_full_filename(band)))
                
                
                try:
                    for i, band in enumerate(self.bands):
                        bands.append(self._read_band(bands_path[i]))
                except IOError as e:
                    exit(e.message, 1)

                src = rasterio.open(bands_path[-1])

                # Get pixel size from source
                self.pixel = src.affine[0]

                # Only collect src data that is needed and delete the rest
                src_data = {
                    'transform': src.transform,
                    'crs': src.crs,
                    'affine': src.affine,
                    'shape': src.shape
                }
                del src

                crn = self._get_boundaries(src_data)

                dst_shape = src_data['shape']
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
                # Delete crn since no longer needed
                del crn

                new_bands = []
                for i in range(0, 3):
                    new_bands.append(numpy.empty(dst_shape, dtype=numpy.float32))

                self.output("Projecting", normal=True, arrow=True)
                for i, band in enumerate(bands):
                    self.output("band %s" % self.bands[i], normal=True, color='green', indent=1)
                    reproject(band, new_bands[i], src_transform=src_data['transform'], src_crs=src_data['crs'],
                              dst_transform=dst_transform, dst_crs=self.dst_crs, resampling=RESAMPLING.nearest)

                # Bands are no longer needed
                del bands
                
            
                self.output("Calculating NDVI", normal=True, arrow=True)
                output_file = '%s_NDVI' % (self.scene)
                
                tilemask = numpy.empty_like(new_bands[-1], dtype=numpy.bool)
                tilemask[(new_bands[1]+new_bands[0]==0)] = True
                new_bands[0]=new_bands[0]*mult_B3+add_B3
                new_bands[1]=new_bands[1]*mult_B4+add_B4
                ndvi=numpy.true_divide((new_bands[1]-new_bands[0]),(new_bands[1]+new_bands[0]))
                ndvi=((ndvi+1)*255 / 2).astype(numpy.uint8)
                ndvi[tilemask]=0
                
                if cmask:
                     # clouds are indicated when Bit 15&16 = 11 or 10
                     ndvi[(new_bands[-1].astype(numpy.uint16) & 49152)>=32768]=0
                     # cirrus are indicated when Bit 13&14 = 11 or 10
                     ndvi[(new_bands[-1].astype(numpy.uint16) & 12288)>=8192]=0

                
                self.output("Final Steps", normal=True, arrow=True)
                
                if mode=='grey':
                    output_file += '_grey.TIF'
                    output_file = join(self.dst_path, output_file) 
                    output = rasterio.open(output_file, 'w', driver='GTiff',
                                           width=dst_shape[1], height=dst_shape[0],
                                           count=1, dtype=numpy.uint8,
                                           nodata=0, transform=dst_transform,
                                           crs=self.dst_crs)
                    self.output("Writing to file", normal=True, color='green', indent=1)                     
                    output.write_band(1, ndvi)
                    
                elif mode=='color':
                    self.output("Converting to RGB", normal=True, color='green', indent=1)                       
                    output_file += '_color.TIF'
                    output_file = join(self.dst_path, output_file) 
                    rgb=self._index2rgb(index_matrix=ndvi)
                    del ndvi
    
                    output = rasterio.open(output_file, 'w', driver='GTiff',
                                           width=dst_shape[1], height=dst_shape[0],
                                           count=3, dtype=numpy.uint8,
                                           nodata=0, transform=dst_transform, photometric='RGB',
                                           crs=self.dst_crs)
                    
                    self.output("Writing to file", normal=True, color='green', indent=1)                       
                    for i in range(0, 3):
                        output.write_band(i+1, rgb[i])
                        
                #colorbar
                    self.output("Creating colorbar", normal=True, color='green', indent=1)
                    output_file2 = '%s_colorbar.png' % (self.scene)
                    output_file2 = join(self.dst_path, output_file2) 
                    colorrange=numpy.array(range(0,256))
                    colorbar=self._index2rgb(index_matrix=colorrange)
                    rgbArray = numpy.zeros((1,256,3), 'uint8')
                    rgbArray[..., 0] = colorbar[0]
                    rgbArray[..., 1] = colorbar[1]
                    rgbArray[..., 2] = colorbar[2]
                    rgbArray=rgbArray.repeat(30,0)
                    
                    cbfig=pyplot.figure(figsize=(10,1.5))
                    image = pyplot.imshow(rgbArray,extent=[-1,1,0,1],aspect=0.1)
                    pyplot.xticks(numpy.arange(-1,1.1,0.2))
                    pyplot.xlabel('NDVI')
                    pyplot.yticks([])
                    pyplot.savefig(output_file2,dpi=300, bbox_inches='tight', transparent=True)
            
                return output_file

    def _pansharpenning(self, bands):

        self.output("Pansharpening", normal=True, arrow=True)
        # Pan sharpening
        m = sum(bands[:3])
        m = m + 0.1

        self.output("calculating pan ratio", normal=True, color='green', indent=1)
        pan = 1/m * bands[-1]

        del m
        del bands[-1]
        self.output("computing bands", normal=True, color='green', indent=1)

        for i, band in enumerate(bands):
            bands[i] = band * pan

        del pan

        return bands

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

    def _read_band(self, band_path):
        """ Reads a band with rasterio """
        return rasterio.open(band_path).read_band(1)
        
        
    def _index2rgb(self, index_matrix):
        """ converts a 8bit matrix to rgb values according to the colormap """
         
        self._read_cmap()
        translate_colormap = numpy.vectorize(self._get_color, otypes=[numpy.uint8])
        rgb_bands = []
        for i in range(3):
            rgb_bands.append(translate_colormap(index_matrix, i))
       
        return rgb_bands
        
    def _get_color(self, n,v=-1):
        if v==-1:
            return self.colormap[n]
        else:
            return self.colormap[n][v]
            
    def _read_cmap(self):
        try:
            i=0
            colormap={0 : (0, 0, 0)}
            with open(settings.COLORMAP) as cmap:
                lines = cmap.readlines()
                for line in lines:
                    if i ==  0 and 'mode = ' in line:
                        i=1
                        maxval = float(line.replace('mode = ', ''))
                    elif i > 0:
                        str = line.split()
                        if str==[]:
                            break
                        colormap.update({i : (int(round(float(str[0])*255/maxval)),
                                      int(round(float(str[1])*255/maxval)),
                                      int(round(float(str[2])*255/maxval)),
                                      )})
                        i += 1
        except IOError:
            pass
    
        colormap = {k: v[:4] for k, v in colormap.iteritems()}
        self.colormap=colormap
    

    def _rescale(self, bands):
        """ Rescale bands """
        self.output("Rescaling", normal=True, arrow=True)

        for key, band in enumerate(bands):
            self.output("band %s" % self.bands[key], normal=True, color='green', indent=1)
            bands[key] = sktransform.rescale(band, 2)
            bands[key] = (bands[key] * 65535).astype('uint16')

        return bands

    def _get_boundaries(self, src):

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

        return output

    def _percent_cut(self, color, low, high):
        return numpy.percentile(color[numpy.logical_and(color > 0, color < 65535)], (low, high))

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


if __name__ == '__main__':

    with timer():
        p = Process(sys.argv[1])

        print p.run(sys.argv[2] == 't')
