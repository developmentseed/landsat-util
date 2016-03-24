FROM    ubuntu:14.04
RUN     apt-get -y update
RUN     apt-get install --yes git-core python-pip python-skimage python-numpy python-scipy libgdal-dev libatlas-base-dev gfortran libfreetype6-dev libglib2.0-dev zlib1g-dev python-pycurl
ADD     . /landsat
RUN     pip install setuptools
RUN     pip install -U pip
RUN     pip install wheel
RUN     cd /landsat && pip install -r requirements-dev.txt
RUN     sed -i 's/numpy.*//g' /landsat/requirements.txt
RUN     sed -i 's/scipy.*//g' /landsat/requirements.txt
RUN     sed -i 's/scikit-image.*//g' /landsat/requirements.txt
RUN     sed -i 's/matplotlib.*//g' /landsat/requirements.txt
RUN     cd /landsat && pip install -e .
