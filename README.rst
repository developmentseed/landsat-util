Landsat-util
===============

.. image:: https://travis-ci.org/developmentseed/landsat-util.svg?branch=v0.5
    :target: https://travis-ci.org/developmentseed/landsat-util

.. image:: https://pypip.in/version/landsat-util/badge.svg
    :target: https://pypi.python.org/pypi/landsat-util/
    :alt: Latest Version

.. image:: https://pypip.in/download/landsat-util/badge.svg
    :target: https://pypi.python.org/pypi/landsat-util/
    :alt: Downloads

.. image:: https://pypip.in/wheel/landsat-util/badge.svg
    :target: https://pypi.python.org/pypi/landsat-util/
    :alt: Wheel Status

.. image:: https://pypip.in/license/landsat-util/badge.svg
    :target: https://pypi.python.org/pypi/landsat-util/
    :alt: License

Landsat-util is a command line utility that makes it easy to search, download, and process Landsat imagery. It uses Development Seed's `API for Landsat Metadata <https://github.com/developmentseed/landsat-api>`_,  which is accessible here: https://api.developmentseed.org/landsat

Landsat-util requires at least 2GM of memory (RAM).

Installation
============

Use pip to install landsat-util. If you are not using virtualenv, you might have to run ``pip`` as ``sudo``.

**OSX**

::
    
    $ pip install landsat-util

**Ubuntu 14.04**

::

    $ sudo apt-get update
    $ sudo apt-get install python-pip python-numpy python-scipy libgdal-dev libatlas-base-dev gfortran
    $ pip install landsat-util
    
**Other systems**

Make sure Python ``setuptools`` is installed.

::

  $ pip install numpy six
  $ python setup.py install

**Upgrading**

::
    
    $ pip install -U landsat-util

If you've previously installed landsat-util with homebrew, first run:

::
  
  $ brew uninstall landsat-util

**Testing**

::

  $ pip install -U requirements/dev.txt
  $ nosetests

Or

::

    $ python setup.py test
  

Overview: What can landsat-util do?
====================================

Landsat-util has three main functions, each of which are performed separately.

- **Search** for landsat tiles based on several search parameters.
- **Download** landsat images.
- **Image processing** and pansharpening of landsat images.

**Help**: Type ``landsat -h`` for detailed usage parameters.

Step 1: Search
++++++++++++++

**Search** returns information about all of the available Landsat tiles that match your criteria, including a link to an unprocessed preview of the tile.  The preview allows you to quickly verify that your area of interest isn't obscured by clouds. The **sceneID** is typically the most important result; you'll need it to to download the tile (see step 2 below).

Search by latitude and longitude:

::

    $ landsat search --lat 38.9004204 --lon -77.0237117

Search by path and row:

::

    $ landsat search -p 009, 045

Advanced filters:

Additionally, it's possible to filter your search using the following parameters:

- **Start and end dates** for when imagery was taken.
- **Maximum percent cloud cover** (default is 20%).

::

    $ landsat search --cloud 4 --start "january 1 2014" --end "january 10 2014" -p 009, 045


Step 2: Download
++++++++++++++++

Download tiles using their unique sceneID, which you can get using ``landsat search``

By default, landsat-util will download a zip file that includes all of the available bands. Alternatively, you can download a subset of the available bands. In this case, landsat-util only downloads those bands if they are available online.

Download images by their custom sceneID, which you get from landsat search:

::

    $ landsat download LC80090452014008LGN00

Download only bands 4, 3 and 2 for a particular sceneID:

::

    $ landsat download LC80090452014008LGN00 --bands 432

Download multiple sceneIDs:

::

    $ landsat download LC80090452014008LGN00 LC80090452015008LGN00 LC80090452013008LGN00

By default downloaded and processed images are saved to the ``~/landsat`` directory.

It's also possible to save the files to an `Amazon S3 bucket <https://aws.amazon.com/s3/>`_, Amazon S3 bucket, by passing in the following optional parameters:

--key           Access Key (Can also be set as an environmental variable as AWS_ACCESS_KEY_ID)
--secret        Secret Key (Can also be set as an environmental variable as AWS_SECRET_ACCESS_KEY)
--bucket        Bucket name (required if uploading to s3)
--region        URL to S3 region e.g. s3-us-west-2.amazonaws.com


Step 3: Image processing
++++++++++++++++++++++++

Landsat-util processes the downloaded tiles using our custom image processing algorithms. By default, bands 4, 3, and 2 will be used to create Natural color imagery. Optionally, you can choose to pansharpen the images, and can also pass in custom band combinations.

Image processing is a very heavy and resource consuming task. Each process takes about 5-10 mins. We recommend that you run the processes in smaller badges. Pansharpening, while increasing image resolution 2x, substantially increases processing time.

Process an archive:

::

    $ landsat process path/to/LC80090452014008LGN00.tar.bz

Process an extracted archive:

::

    $ landsat process path/to/LC80090452014008LGN00

Process a color infrared image using bands 5, 4 and 3:

::

    $ landsat process path/to/LC80090452014008LGN00  --bands 543

Process and pansharpen an image:

::

    $ landsat process path/to/LC80090452014008LGN00.tar.bz --pansharpen


Recent changes:
===============

- Add longitude latitude search
- Improve console output
- Add more color options such as false color, true color, etc.

Todo:
=====

- Add Sphinx Documentation
- Add capacity for NDVI output
- Add alternative projections (currently only option is default web-mercator; EPSG: 3857)
- Connect search to Google Address API
- Include 16-bit image variant in output
- Add support for color correct looping over multiple compressed inputs (currently just 1)
