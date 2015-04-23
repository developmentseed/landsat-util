Landsat-util
===============

.. image:: https://travis-ci.org/developmentseed/landsat-util.svg?branch=v0.5
    :target: https://travis-ci.org/developmentseed/landsat-util

Landsat-util is a command line utility that makes it easy to search, download, and process Landsat imagery.

This tool uses Development Seed's `API for Landsat Metadata <https://github.com/developmentseed/landsat-api>`_.

This API is accessible here: https://api.developmentseed.org/landsat

You can also run your own API and connect it to this tool.

Installation
============

**On Mac**

  ``$: pip install landsat-util``

**On Ubuntu 14.04**

Use pip to install landsat-util. If you are not using virtualenv, you might have to run ``pip`` as ``sudo``.

  ``$: sudo apt-get update``
  ``$: sudo apt-get install python-pip python-numpy python-scipy libgdal-dev libatlas-base-dev gfortran``
  ``$: pip install landsat-util``

**On Other systems**

  ``$: python setup.py numpy six``
  ``$: python setup.py install``


**To Upgrade**

  ``$: pip install -U landsat-util``

If you have installed previous version of landsat using brew, first run:

  ``$: brew uninstall landsat-util``

**To Test**

  ``$: pip install -U requirements/dev.txt``
  ``$: nosetests``

Overview: What can landsat-util do?
====================================

Landsat-util has three main functions:

- **Search** for landsat tiles based on several search parameters.
- **Download** landsat images.
- **Image processing** and pan sharpening on landsat images.

These three functions have to be performed separately.

**Help**: Type ``landsat -h`` for detailed usage parameters.

Step 1: Search
===============

Search returns information about all landsat tiles that match your criteria.  This includes a link to an unprocessed preview of the tile.  The most important result is the tile's *sceneID*, which you will need to download the tile (see step 2 below).

Search for landsat tiles in a given geographical region, using any of the following:

- **Paths and rows**: If you know the paths and rows you want to search for.
- **Latidue and Longitude**: If you need the latitude and longitude of the point you want to search for.

Additionally filter your search using the following parameters:

- **Start and end dates** for when imagery was taken
- **Maximum percent cloud cover** (default is 20%)

**Examples of search**:

Search by path and row:

``$: landsat search --cloud 4 --start "january 1 2014" --end "january 10 2014" -p 009,045``

Search by latitude and longitude:

``$: landsat search --lat 38.9004204 --lon -77.0237117``


Step 2: Download
=================

You can download tiles using their unique sceneID, which you get from landsat search.

Landsat-util will download a zip file that includes all the bands. You have the option of specifying the bands you want to down. In this case, landsat-util only downloads those bands if they are available online.

**Examples of download**:

Download images by their custom sceneID, which you get from landsat search:

``$: landsat download LC80090452014008LGN00``

Download only band 4, 3 and 2 for a particular sceneID:

``$: landsat download LC80090452014008LGN00 --bands 432``

Download multiple sceneIDs:

``$: landsat download LC80090452014008LGN00 LC80090452015008LGN00 LC80090452013008LGN00``

Step 3: Image processing
=========================

You can process your downloaded tiles with our custom image processing algorithms.  In addition, you can choose to pansharpen your images and specify which bands to process.

**Examples of image processing**:

Process images that are already downloaded. Remember, the program accepts both zip files and unzipped folders:

``$: landsat process path/to/LC80090452014008LGN00.tar.bz``

If unzipped:

``$: landsat process path/to/LC80090452014008LGN00``

Specify bands 3, 5 and 1:

``$: landsat process path/to/LC80090452014008LGN00  --bands 351``

Process *and* pansharpen a downloaded image:

``$: landsat process path/to/LC80090452014008LGN00.tar.bz --pansharpen``


Important Notes
===============

- All downloaded and processed images are stored at your home directory in landsat forlder: ``~/landsat``

- The image thumbnail web address that is included in the results can be used to make sure that clouds are not obscuring the subject of interest. Run the search again if you need to narrow down your result and then start downloading images. Each image is usually more than 700mb and it might takes a very long time if there are too many images to download

- Image processing is a very heavy and resource consuming task. Each process takes about 5-10 mins. We recommend that you run the processes in smaller badges. Pansharpening, while increasing image resolution 2x, substantially increases processing time.

- Landsat-util requires at least 2GB of Memory (RAM).

Recently Added
+++++++++++++++

- Add longitude latitude search
- Improve console output
- Add more color options such as false color, true color, etc.


To Do List
++++++++++

- Add Sphinx Documentation
- Add capacity for NDVI output
- Add alternative projections (currently only option is default web-mercator; EPSG: 3857)
- Connect search to Google Address API
- Include 16-bit image variant in output
- Add support for color correct looping over multiple compressed inputs (currently just 1)
