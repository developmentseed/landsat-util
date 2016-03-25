FROM    ubuntu:14.04
RUN     apt-get -y update
RUN     apt-get install --yes git-core python-pip python-scipy libgdal-dev libatlas-base-dev gfortran libfreetype6-dev libglib2.0-dev zlib1g-dev python-pycurl
ADD     . /landsat
RUN     pip install setuptools
RUN     pip install -U pip
RUN     pip install wheel
RUN     pip install https://s3-us-west-2.amazonaws.com/ds-satellite-projects/landsat-util/numpy-1.10.4-cp27-cp27mu-linux_x86_64.whl
RUN     pip install https://s3-us-west-2.amazonaws.com/ds-satellite-projects/landsat-util/Pillow-3.1.1-cp27-cp27mu-linux_x86_64.whl
RUN     pip install https://s3-us-west-2.amazonaws.com/ds-satellite-projects/landsat-util/scikit_image-0.12.3-cp27-cp27mu-manylinux1_x86_64.whl
RUN     cd /landsat && pip install -r requirements-dev.txt
RUN     sed -i 's/numpy.*//g' /landsat/requirements.txt
RUN     sed -i 's/scipy.*//g' /landsat/requirements.txt
RUN     sed -i 's/scikit-image.*//g' /landsat/requirements.txt
RUN     cd /landsat && pip install -e .
