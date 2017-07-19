FROM    ubuntu:14.04
RUN     apt-get -y update
RUN     apt-get install --yes curl libgdal-dev python3-dev build-essential
ADD     . /landsat
RUN     curl -O https://bootstrap.pypa.io/get-pip.py
RUN     python3 get-pip.py
RUN     pip3 install numpy
RUN     cd /landsat && pip install -r requirements-dev.txt
RUN     cd /landsat && pip install -e .
