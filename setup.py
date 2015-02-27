#!/usr/bin/env python

# Landsat Util
# License: CC0 1.0 Universal

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def readme():
    with open("README.rst") as f:
        return f.read()

setup(
    name="landsat",
    version='0.4.5',
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
      "requests==2.5.3",
      "python-dateutil==2.2",
      "numpy==1.9.1",
      "termcolor==1.1.0",
      "rasterio==0.18",
      "six==1.9.0",
      "scikit-image==0.10.1",
      "homura==0.1.0"
    ],
)
