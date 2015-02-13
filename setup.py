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
if subprocess.call(['which', 'gdal-config']):
    error = """Error: gdal-config is not installed on this machine.
This installation requires gdal-config to proceed.

If you are on Mac OSX, you can installed gdal-config by running:
    brew install gdal

On Ubuntu you should run:
    sudo apt-get install libgdal1-dev

Exiting the setup now!"""
    print error

    sys.exit(1)


def readme():
    with open("README.rst") as f:
        return f.read()

setup(name="landsat",
      version='0.2.0',
      description="A utility to search, download and process Landsat 8" +
      " satellite imagery",
      long_description=readme(),
      author="Scisco",
      author_email="alireza@developmentseed.org",
      scripts=["bin/landsat"],
      url="https://github.com/developmentseed/landsat-util",
      packages=["landsat"],
      include_package_data=True,
      license="CCO",
      platforms="Posix; MacOS X; Windows",
      install_requires=[
          "GDAL>=1.11",
          "elasticsearch==1.1.1",
          "gsutil==4.4",
          "requests==2.3.0",
          "python-dateutil==2.2",
          "numpy"
      ],
      )
