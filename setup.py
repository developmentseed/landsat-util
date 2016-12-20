#!/usr/bin/env python

# Landsat Util
# License: CC0 1.0 Universal

try:
    from setuptools import setup
    setup_kwargs = {'entry_points': {'console_scripts':['landsat=landsat.landsat:__main__']}}
except ImportError:
    from distutils.core import setup
    setup_kwargs = {'scripts': ['bin/landsat']}
    

from landsat import __version__


def readme():
    with open('README.rst') as f:
        return f.read()

with open('requirements.txt') as fid:
    INSTALL_REQUIRES = [l.strip() for l in fid.readlines() if l]

with open('requirements-dev.txt') as fid:
    TEST_REQUIRES = [l.strip() for l in fid.readlines() if l]

setup(
    name='landsat-util',
    version=__version__,
    description='A utility to search, download and process Landsat 8' +
    ' satellite imagery',
    long_description=readme(),
    author='Development Seed',
    author_email='info@developmentseed.org',
    url='https://github.com/developmentseed/landsat-util',
    packages=['landsat'],
    include_package_data=True,
    license='CCO',
    platforms='Posix; MacOS X; Windows',
    install_requires=INSTALL_REQUIRES,
    test_suite='nose.collector',
    tests_require=TEST_REQUIRES,
    **setup_kwargs
)
