#!/usr/bin/env python

# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco
#
# License: CC0 1.0 Universal

import sys
import subprocess

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Check if gdal-config is installed
if subprocess(['which', 'gdal-config']):
    print "Error: gdal-config is not installed on this machine."
    print "This installation requires gdal-config to proceed."
    print ""
    print "If you are on Mac OSX, you can installed gdal-config by running" + \
          "brew install gdal"
    print "On Ubuntu you should run sudo apt-get install libgdal1-dev"
    print "Exiting the setup now!"
    sys.exit(1)


def readme():
    with open("README.md") as f:
        return f.read()

setup(name="landsat",
      version='0.1.0',
      description="A utility to search, download and process Landsat 8" +
      " satellite imagery",
      long_description=readme(),
      author="Scisco",
      author_email="alireza@developmentseed.org",
      scripts=["bin/landsat"],
      url="https://github.com/developmentseed/landsat-util",
      packages=["landsat"],

      license="CCO",
      platforms="Posix; MacOS X; Windows",
      install_requires=[
          "GDAL==1.11.0",
          "elasticsearch==1.1.1",
          "gsutil==4.4",
      ],
      )
