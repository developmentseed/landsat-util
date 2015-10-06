FROM    ubuntu:14.04
RUN     apt-get -y update
RUN     apt-get install --yes python-pip python-skimage python-numpy python-scipy libgdal-dev libatlas-base-dev gfortran libfreetype6-dev libglib2.0-dev zlib1g-dev python-pycurl
ADD     landsat /usr/local/lib/python2.7/dist-packages/landsat
ADD     bin/landsat /usr/local/bin/
ADD     . /landsat
RUN     cd /landsat && pip install -r requirements/base.txt

