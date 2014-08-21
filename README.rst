Landsat Utility
===============

A utility to search, download and process Landsat 8 satellite imagery.

This tool uses Development Seed's `API for Landsat Metdata <https://github.com/developmentseed/landsat-api>`_.

This API is accessible here: http://api.developmentseed.com:8000/landsat

You can also run your own API and connect it to this tool.

Installation
============

**On Mac**

You need to install gdal before using this tool. You can try brew:

.. code-block:: console

    $: brew udpate
    $: brew install gdal

**On Ubuntu (Tested on Ubuntu 14.04)**

Install PIP and some other  dependencies for a successful install of requirements.txt

.. code-block:: console

    $: sudo apt-add-repository ppa:ubuntugis/ubuntugis-unstable
    $: sudo apt-get update
    $: sudo apt-get install python-pip build-essential libssl-dev libffi-dev python-dev python-gdal -y

**Install Landsat-util**

Either use pip or easy_install to install the utility:

.. code-block:: console

    $: pip install -U git+git://github.com/developmentseed/landsat-util.git

or download the repository and run:

.. code-block:: console

    $: python setup.py install

**Update Landsat-util**

.. code-block:: console

    $: pip install -U git+git://github.com/developmentseed/landsat-util.git

Usage
=====

.. code-block:: console

    $: landsat -h

.. code-block:: console

   Usage:
        Landsat-util helps you with searching Landsat8 metadata and downloading the
        images within the search criteria.

        With landsat-util you can also find rows and paths of an area by searching
        a country name or using a custom shapefile and use the result to further
        narrow your search.

        Syntax:
        landsat.py [OPTIONS]

        Example uses:
        To search and download images or row 003 and path 003 with a data range
        with cloud coverage of maximum 3.0%:
            landsat.py -s 01/01/2014 -e 06/01/2014 -l 100 -c 3 -i "003,003"


    Options:
      -h, --help            show this help message and exit

      Search:
        To search Landsat's Metadata use these options:

        -i "path,row,path,row, ... ", --rows_paths="path,row,path,row, ... "
                            Include a search array in this
                            format:"path,row,path,row, ... "

        -s 01/27/2014, --start=01/27/2014
                        Start Date - Format: MM/DD/YYYY
        -e 02/27/2014, --end=02/27/2014
                            End Date - Format: MM/DD/YYYY
        -c 1.00, --cloud=1.00
                            Maximum cloud percentage
        -l 100, --limit=100
                            Limit results. Max is 100
        -d, --direct        Only search scene_files and don't use the API

      Clipper:
        To find rows and paths of a shapefile or a country use these options:

        -f /path/to/my_shapefile.shp, --shapefile=/path/to/my_shapefile.shp
                            Path to a shapefile for generating the rows andpath.
        -o Italy, --country=Italy
                            Enter country NAME or CODE that will designate imagery
                            area, for a list of country syntax visit:
                            http://goo.gl/8H9wuq

      Metadata Updater:
        Use this option to update Landsat API if you havea local copy running

        -u, --update-metadata
                            Update ElasticSearch Metadata. Requires accessto an
                            Elastic Search instance

**Example**

.. code-block:: console

    $: landsat -m --rows_paths="013,044" --cloud=5 --start=04/01/2014

Make sure to use right format for rows and paths. For example instead of using ``3`` use ``003``.

**Output folder structure**

The output is saved in the home directory of the user

.. code-block:: console

  |-- Home Folder
  |     |-- output
  |     |   |-- imagery
  |     |   |   |-- file_scene
  |     |   |   |-- zip
  |     |   |   |   |-- LC80030032014174LGN00.tar.bz
  |     |   |   |-- unzip
  |     |   |   |   |-- LC80030032014174LGN00
  |     |   |   |   |-- LC80030032014174LGN00_B1.TIF
  |     |   |   |   |-- LC80030032014174LGN00_B2.TIF
  |     |   |   |   |-- LC80030032014174LGN00_B3.TIF
  |     |   |   |   |-- LC80030032014174LGN00_B4.TIF
  |     |   |   |     |-- LC80030032014174LGN00_MTL.txt



