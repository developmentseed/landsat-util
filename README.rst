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

**Installing Landsat8 Utility**

Either use pip or easy_install to install the utility:

.. code-block:: console

    $: pip install landsat

or

.. code-block:: console

    $: sudo easy_install

Usage
=====

.. code-block:: console

    $: landsat -h

.. code-block:: console

   Usage: landsat [options]

   Options:
   -h, --help            show this help message and exit
   -m                    Use Metadata API to search
   --rows_paths="path,row,path,row, ... "
                        Include a search array in this format:
                        "path,row,path,row, ... "
   --start=01/27/2014    Start Date - Format: MM/DD/YYYY
   --end=02/27/2014      End Date - Format: MM/DD/YYYY
   --cloud=1.00          Maximum cloud percentage
   --limit=100           Limit results. Max is 100
   --shapefile=my_shapefile.shp
                        Generate rows and paths from a shapefile. You must
                        create a folder called 'shapefile_input'. You must add
                        your shapefile to this folder.
   --country=Italy       Enter country NAME or CODE that will designate imagery
                        area, for a list of country syntax visit
                        ("https://docs.google.com/spreadsheets/d
                        /1CgC0rrvvT8uF9dgeNMI0CVVqc0z85N-
                        K9cEVnN01aN8/edit?usp=sharing)"
   --update-metadata     Update ElasticSearch Metadata. Requires access
                        to an Elastic Search instance

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
  |     |   |-- Shapefiles
  |     |   |   |-- input
  |     |   |   |-- output


