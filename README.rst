Landsat-util
===============

.. image:: https://travis-ci.org/developmentseed/landsat-util.svg?branch=v0.5
    :target: https://travis-ci.org/developmentseed/landsat-util

.. image:: https://badge.fury.io/py/landsat-util.svg
    :target: http://badge.fury.io/py/landsat-util

.. image:: https://img.shields.io/pypi/dm/landsat-util.svg
    :target: https://pypi.python.org/pypi/landsat-util/
    :alt: Downloads

.. image:: https://img.shields.io/pypi/l/landsat-util.svg
    :target: https://pypi.python.org/pypi/landsat-util/
    :alt: License


Landsat-util is a command line utility that makes it easy to search, download, and process Landsat imagery.

Docs
+++++

For full documentation visit: https://pythonhosted.org/landsat-util/

To run the documentation locally::

    $ pip install -r requirements/dev.txt
    $ cd docs
    $ make html

Travis Tests
++++++++++++

To speed up testing on travis, we use a docker image.

To test with docker image locally run:

.. code::

    $ docker run --rm -it -v "$(pwd)":/test developmentseed/landsat-util:travis nosetests

Recently Added Features
+++++++++++++++++++++++

- Improved pansharpening
- Use BQA bands for cloud/snow coverage and use in color correction
- Add support for different NDVI color maps (three included)
- Add support for image clipping using the new `--clip` flag
- Add alternative projections (currently only option is default web-mercator; EPSG: 3857)

Change Log
++++++++++

See `CHANGES.txt <CHANGES.txt>`_.
