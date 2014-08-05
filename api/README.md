## Landsat-util metadata API

*This is a fork of the excellent OpenFDA API: https://github.com/FDA/openfda/tree/master/api*

## Getting started

### Installing Elastic Search on Ubuntu:

First you need Oracle Java

    $: sudo add-apt-repository ppa:webupd8team/java
    $: sudo apt-get update
    $: sudo apt-get install oracle-java7-installer -y

Then you need to get the latest version of elastic search debian package from [ES website](http://www.elasticsearch.org/download/)

    $: wget https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.3.1.deb
    $: sudo dpkg -i elasticsearch-1.3.1.deb
    $: sudo update-rc.d elasticsearch defaults 95 10
    $: sudo /etc/init.d/elasticsearch start

ES will be accessible on `http://localhost:9200`

#### Installing Elastic Search on Mac

Donwload the lastest version of elastic search zip from [ES website](http://www.elasticsearch.org/download/)

Unzip and run `bin/elasticsearch`

ES will be accessible on `http://localhost:9200`

## Running the API

Install NodeJS, npm and forever (This is ONLY needed if you want to run the API engine)

    $: sudo apt-get install nodejs ruby ruby1.9.1-dev npm -y
    $: sudo ln -s /usr/bin/nodejs /usr/bin/node
    $: npm install

If you want to update the metadata data on Elastic Search, make sure you have followed steps [described here](https://github.com/developmentseed/landsat-util) and then run the below command from the parent folder:

    $: ./landsat_util.py --update-metadata

To run the api:

    $: node api.js

To test the API run:

    $: curl localhost:8000/landsat?search=LC81660362014196LGN00

To run the API in the background run:

    $: forever start api.js

To list forever jobs:

    $: forever list
    info:    Forever processes running
    data:        uid  command         script forever pid   logfile                        uptime
    data:    [0] v0MM /usr/bin/nodejs api.js 19708   19710 /home/ubuntu/.forever/v0MM.log 0:0:5:46.387

To Kill the forever job:

    $: forever stop 0
