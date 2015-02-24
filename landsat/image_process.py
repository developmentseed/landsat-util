# Pansharpened Image Process using Rasterio
# Author: Marc Farra

import os
import subprocess
import sys

import numpy
import rasterio
from rasterio import Affine
from rasterio.warp import reproject, RESAMPLING, transform

from skimage import img_as_ubyte, exposure, img_as_float
from skimage import transform as sktransform

tempdir = './'
scene = sys.argv[2]
tiffname = os.path.join(tempdir, 'landsat-pan.TIF')

with rasterio.drivers():
    with rasterio.open(scene + '_B4.TIF') as band4:
        with rasterio.open(scene + '_B3.TIF') as band3:
            with rasterio.open(scene + '_B2.TIF') as band2:
                with rasterio.open(scene + '_B8.TIF') as band8:
                    src = band8
                    band4_s = band4.read_band(1)
                    band3_s = band3.read_band(1)
                    band2_s = band2.read_band(1)
                    band8_s = band8.read_band(1)

    print ('Getting extent')
    # Get extent and destination filesize
    inProj = {'init':unicode.encode(src.crs['init'])}
    outProj = {'init':'epsg:3857'}
    ulx1, uly1 = src.affine[2], src.affine[5]
    ulx2, uly2 = transform(src.crs, outProj, [ulx1], [uly1])
    lrx1, lry1 = ulx1 + 15 * src.shape[0], uly1 + 15 * src.shape[1]
    lrx2, lry2 = transform(src.crs, outProj, [lrx1], [lry1])
    dst_shape = (int((lrx2[0] - ulx2[0])/15), int((lry2[0] - uly2[0])/15))
    dst_transform = (ulx2[0], 15, 0.0, uly2[0], 0.0, -15)
    dst_crs = {'init': u'epsg:3857'}

    r = numpy.empty(dst_shape, dtype=numpy.uint16)
    g = numpy.empty(dst_shape, dtype=numpy.uint16)
    b = numpy.empty(dst_shape, dtype=numpy.uint16)
    b8 = numpy.empty(dst_shape, dtype=numpy.uint16)

    print('Rescaling')
    print band4_s.shape, band3_s.shape, band2_s.shape
    print ('    > scaling first band')
    band4_s = sktransform.rescale(band4_s, 2)
    band4_s = (band4_s * 65535).astype('uint16')
    print ('    > scaling second band')
    band3_s = sktransform.rescale(band3_s, 2)
    band3_s = (band3_s * 65535).astype('uint16')
    print ('    > scaling third band')
    band2_s = sktransform.rescale(band2_s, 2)
    band2_s = (band2_s * 65535).astype('uint16')
    print band4_s.shape, band3_s.shape, band2_s.shape

    print('Projecting')
    for k, color, band in zip('1238', [r,g,b,b8], [band4_s, band3_s, band2_s, band8_s]):
        print 'projecting band',k
        reproject(band, color, src_transform = src.transform,
            src_crs = src.crs,
            dst_transform = dst_transform, dst_crs = dst_crs,
            resampling = RESAMPLING.nearest)
    
    print('Pan-Sharpening')
  
    # Pan sharpening
    m = r + b + g
    m = m + 0.1
    print ('    > calculating pan ratio')
    pan = 1/m * b8
    print('     > computing bands')
    r = r * pan
    b = b * pan
    g = g * pan

    r = r.astype(numpy.uint16)
    g = g.astype(numpy.uint16)
    b = b.astype(numpy.uint16)
    print r.min(), r.max()

    # Percent cut
    def perc_cut(color):
        return numpy.percentile(color[numpy.logical_and(color > 0, color < 65535)], (2, 98)) 
    
    print('Color Correcting')
    p2r, p98r = perc_cut(r)
    p2g, p98g = perc_cut(g)
    p2b, p98b = perc_cut(b)
    r = exposure.rescale_intensity(r, in_range=(p2r, p98r))
    g = exposure.rescale_intensity(g, in_range=(p2g, p98g))
    b = exposure.rescale_intensity(b, in_range=(p2b, p98b))

    # Gamma correction
    r = exposure.adjust_gamma(r, 1.1)
    b = exposure.adjust_gamma(b, 0.9)

    # Write to output
    print('Writing Output')
    with rasterio.open(
        tiffname,'w', driver='GTiff',
        width=dst_shape[1],height=dst_shape[0],
        count=3,dtype=numpy.uint8,
        nodata=0,
        transform=dst_transform,
        photometric='RGB',
        crs=dst_crs) as dst:
        for k, arr in [(1, r), (2, g), (3, b)]:
            dst.write_band(k, img_as_ubyte(arr))
            
info = subprocess.call(['open', tiffname])