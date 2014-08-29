Landsat-util
===============

Landsat-util is a command line utility that makes it easy to search, download, and process Landsat imagery.

This tool uses Development Seed's `API for Landsat Metdata <https://github.com/developmentseed/landsat-api>`_.

This API is accessible here: http://api.developmentseed.com:8000/landsat

You can also run your own API and connect it to this tool.

Installation
============

**On Mac**

Use brew to install landsat-util:

.. code-block:: console

  $: brew install https://raw.githubusercontent.com/developmentseed/landsat-util/master/Formula/landsat-util.rb

For the dev version try:

.. code-block:: console

  $: brew install https://raw.githubusercontent.com/developmentseed/landsat-util/master/Formula/landsat-util.rb --HEAD

**On Ubuntu**

Use pip to install landsat-util:

.. code-block:: console

    $: sudo apt-add-repository ppa:ubuntugis/ubuntugis-unstable
    $: sudo apt-get update
    $: sudo apt-get install git python-pip build-essential libssl-dev libffi-dev python-dev python-gdal libgdal1-dev gdal-bin -y
    $: sudo pip install -U git+git://github.com/developmentseed/landsat-util.git

**On Other systems**

Make sure you have these dependencies:

- GDAL
- ImageMagick
- Orfeo-40

Then Run:

.. code-block:: console

    $: pip install -U git+git://github.com/developmentseed/landsat-util.git

Alternatively, you can also download the package and run:

.. code-block:: console

    $: python setup.py install

Usage
=====

.. code-block:: console

    $: landsat -h

**Search**

To search paths and rows with date and cloud coverage limit and download images

.. code-block:: console

    $: landsat search --download --cloud 6 --start "july 01 2014" --end "august 1 2014" pr 165 100

To only search the rows and paths but not to download

.. code-block:: console

    $: landsat search --cloud 6 --start "july 01 2014" --end "august 1 2014" pr 165 100

To find rows and paths in a shapefile and download with dates and cloud coverage
- We recommend [geojson.io](http://geojson.io/#map=2/20.0/0.0) for shapefile generation (quicker and easier than using GIS software)

.. code-block:: console

    $: landsat search --download --cloud 6 --start "july 01 2014" --end "august 1 2014" shapefile path/to/shapefile.shp

To find rows and paths in a shapefile and download and process images all together

.. code-block:: console

    $: landsat search --imageprocess --cloud 6 --start "july 01 2014" --end "august 1 2014" shapefile path/to/shapefile.shp

To find rows and paths of a country and download images (The full list is http://goo.gl/8H9wuq)

.. code-block:: console

    $: landsat search --cloud 6 --start "july 01 2014" --end "august 1 2014" country Singapore

**Download**

To download scene images directily

.. code-block:: console

    $: landsat download LC80030032014142LGN00 LC80030032014158LGN00

**Image Process**

To process images that are aleady downloaded. Remember, the system only accepts zip files

.. code-block:: console

    $: landsat process path/to/LC80030032014158LGN00.tar.bz

To pan sharpen the image

.. code-block:: console

    $: landsat process --pansharpen path/to/LC80030032014158LGN00.tar.bz


Important Notes
===============

- All downloaded and processed images are stored at your home directory in landsat forlder: ``~/landsat``

- If you are not sure what images you are looking for, make sure to use ``--onlysearch`` flag to view the results first. The image thumbnail web address that is included in the results can be used to make sure that clouds are not obscuring the subject of interest. Run the search again if you need to narrow down your result and then start downloading images. Each image is usually more than 700mb and it might takes a very long time if there are too many images to download

- Image processing is a very heavy and resource consuming task. Each process takes about 20-30 mins. We recommend that you run the processes in smaller badges. Pansharpening, while increasing image resolution 2x, substantially increases processing time.

- Country based search queries can return a large number of images; for countries that return large search results we recommend selecting best imagery based on thumbnails and then using the download tool to install specific imagery based on Landsat scene ID.

To Do List
++++++++++

- Add longitude latitude search
- Add Sphinx Documentation
- Improve console output
- Add more color options such as false color, true color, etc.
- Add capacity for NDVI output
- Add alternative projections (currently only option is default web-mercator; EPSG: 3857)
- Connect search to Google Address API
- Include 16-bit image variant in output
- Add support for color correct looping over multiple compressed inputs (currently just 1)
