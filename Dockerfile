FROM developmentseed/geolambda:full

#RUN \
#    yum install -y openssl-devel

ENV \
    PYCURL_SSL_LIBRARY=nss

WORKDIR /build

COPY requirements*txt /build/

RUN \
    pip-3.6 install -r requirements.txt; \
    pip-3.6 install -r requirements-dev.txt;

COPY . /build/

RUN pip-3.6 install .

WORKDIR /home/geolambda
