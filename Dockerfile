FROM    ubuntu:14.10
RUN     apt-get -y update
RUN     apt-get install --yes python-pip python-numpy python-scipy libgdal-dev libatlas-base-dev gfortran libfreetype6-dev libglib2.0-dev zlib1g-dev python-pycurl
RUN     pip install landsat-util
