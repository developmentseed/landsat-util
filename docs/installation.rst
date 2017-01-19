Installation
===============

Mac OSX
++++++++

::

    $: pip install landsat-util

Ubuntu 14.04
++++++++++++

Use pip to install landsat-util. If you are not using virtualenv, you might have to run ``pip`` as ``sudo``::

    $: sudo apt-get update
    $: sudo apt-get install python-pip python-numpy python-scipy libgdal-dev libatlas-base-dev gfortran libfreetype6-dev
    $: pip install landsat-util

Other systems
+++++++++++++

Make sure Python setuptools is installed::

    $: python setup.py numpy six
    $: python setup.py install

Docker
++++++

If you have docker installed, you can use landsat-util image on docker::

    $: docker pull developmentseed/landsat-util
    $: docker run -it developmentseed/landsat-util:latest /bin/sh -c "landsat -h"

To use docker version run::

    $: docker run -it -v ~/landsat:/root/landsat developmentseed/landsat-util:latest landsat -h

Example commands::

    $: docker run -it -v ~/landsat:/root/landsat developmentseed/landsat-util:latest landsat search --cloud 4 --start "january 1 2014" --end "january 10 2014" -p 009,045
    $: docker run -it -v ~/landsat:/root/landsat developmentseed/landsat-util:latest landsat download LC80090452014008LGN00 --bands 432

This commands mounts ``landsat`` folder in your home directory to ``/root/landsat`` in docker. All downloaded and processed images are stored in ``~/landsat`` folder of your computer.

If you are using Windows replace ``~/landsat`` with ``/c/Users/<path>``.


Upgrade
+++++++

::

    $: pip install -U landsat-util

If you have installed a previous version of landsat using brew, first run::

    $: brew uninstall landsat-util

Running Tests
+++++++++++++

::

    $: pip install -r requirements-dev.txt
    $: python setup.py test

