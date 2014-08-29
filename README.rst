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

Overview: What can landsat-util do?
============
Landsat-util has three main functions:

- **Search** for landsat tiles based on several search parameters.
- **Download** landsat images.
- **Image processing** and pan sharpening on landsat images.

These three functions can be performed separately or all at once.

**Help**: Type ``landsat -h`` for detailed usage parameters.

Step 1: Search
============

Search returns information about all landsat tiles that match your criteria.  This includes a link to an unprocessed preview of the tile.  The most important result is the tile's *sceneID*, which you will need to download the tile (see step 2 below).

Search for landsat tiles in a given geographical region, using any of the following:

- **Paths and rows**: If you know the paths and rows you want to search for.
- **Country name**: If you know what country you want imagery for.
- **Custom shapefile**: Use a tool such as http://geojson.io/ to generate custom shapefiles bounding your geographical region of interest.  Landsat-util will download tiles within this shapefile.

Additionally filter your search using the following parameters:

- **Start and end dates** for when imagery was taken
- **Maximum percent cloud cover** (default is 20%)

**Examples of search**:

Search by path and row:

``$: landsat search --cloud 6 --start "july 01 2014" --end "august 1 2014" pr 165 100``

Search by country (The full list of countries is http://goo.gl/8H9wuq):
 
``$: landsat search --cloud 6 --start "july 01 2014" --end "august 1 2014" country 'Singapore'``

Search by custom shapefile:

``$: landsat search --cloud 6 --start "july 01 2014" --end "august 1 2014" shapefile path/to/shapefile.shp``

Step 2: Download
============

You can download tiles using their unique sceneID, which you get from landsat search.

**Examples of download**:

Download images by their custom sceneID, which you get from landsat search:

``$: landsat download LC80030032014142LGN00 LC80030032014158LGN00``

Search and download tiles all at once with the --download flag:

``$: landsat search --download --cloud 6 --start "july 01 2014" --end "august 1 2014" pr 165 100``

Step 3: Image processing
============

You can process your downloaded tiles with our custom image processing algorithms.  In addition, you can choose to pansharpen your images.

**Examples of image processing**:

Process images that are already downloaded. Remember, the program only accepts zip files:

``$: landsat process path/to/LC80030032014158LGN00.tar.bz``

Process *and* pansharpen a downloaded image:

``$: landsat process --pansharpen path/to/LC80030032014158LGN00.tar.bz``

Search, download, and process images all at once using the --imageprocess flag:

``$: landsat search --imageprocess --cloud 6 --start "july 01 2014" --end "august 1 2014" shapefile path/to/shapefile.shp``


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
