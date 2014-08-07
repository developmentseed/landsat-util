#!/usr/bin/env python

# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco
#
# License: CC0 1.0 Universal

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def readme():
    with open("README.md") as f:
        return f.read()

setup(name = "landsat",
    version = '0.1.0',
    description = "A utility to search, download and process Landsat 8" +
                " satellite imagery",
    long_description = readme(),
    author = "Scisco",
    author_email = "alireza@developmentseed.org",
    scripts = ["bin/landsat"],
    url = "https://github.com/developmentseed/landsat-util",
    packages = ["landsat"],

    license = "CCO",
    platforms = "Posix; MacOS X; Windows",
    install_requires=[
        "GDAL==1.11.0",
        "elasticsearch==1.1.1",
        "gsutil==4.4",
    ],
)
