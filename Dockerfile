FROM ubuntu:trusty

# install
RUN apt-get install -y software-properties-common
RUN apt-add-repository ppa:ubuntugis/ubuntugis-unstable
RUN apt-get update && apt-get install -y git python-pip build-essential libssl-dev libffi-dev python-dev python-gdal libgdal1-dev gdal-bin imagemagick geotiff-bin
RUN pip install -U git+git://github.com/developmentseed/landsat-util.git

# clean
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
