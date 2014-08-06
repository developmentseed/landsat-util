# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco
#
# License: CC0 1.0 Universal

#
# This is intended to populate an Elastic Search instance.
# For this file to work, you must make sure that you have a running instnace
# of Elastic Search and it is setup in the settings.py

from __future__ import print_function

import sys
import json
from urllib2 import urlopen, HTTPError, URLError


from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError

import settings


class Metadata(object):

    def __init__(self):
        self.l8_metadata_filename = settings.L8_METADATA_FILENAME
        self.l8_metadata_url = settings.L8_METADATA_URL
        self.assests_dir = settings.ASSESTS_DIR
        self.es_url = settings.ES_URL
        self.es_main_index = settings.ES_MAIN_INDEX
        self.es_main_type = settings.ES_MAIN_TYPE

    def populate(self):
        if self.download():
            es = Elasticsearch(self.es_url)

            f = open('%s/%s' % (self.assests_dir, self.l8_metadata_filename),
                     'r')
            # Read the first line for all the headers
            headers = f.readline().split(',')

            # Read the rest of the document
            rows = f.readlines()
            added_counter = 0
            skipped_counter = 0
            for row in rows:
                fields = row.split(',')
                obj = {}
                for header in headers:
                    try:
                        obj[header.replace('\n', '')] = float(fields[
                            headers.index(header)].replace('\n', ''))
                    except ValueError:
                        obj[header.replace('\n', '')] = fields[
                            headers.index(header)].replace('\n', '')
                try:
                    if not es.exists(
                            index=self.es_main_index,
                            doc_type=self.es_main_type,
                            id=obj['sceneID']):
                        es.create(
                            index=self.es_main_index,
                            doc_type=self.es_main_type,
                            id=obj['sceneID'],
                            body=json.dumps(obj),
                            ignore=409)
                        # print('%s-%s created' % (counter, obj['sceneID']))
                        added_counter += 1
                        print('%s new records added' % added_counter,
                              end='\r')
                    else:
                        skipped_counter += 1

                    # New meta data is added to the top of the document.
                    # When the script starts to see existing records, it means
                    # that all new records are added and it's safe to break
                    # the loop.
                    if skipped_counter > 10:
                        break

                except ConnectionError:
                    print('There was a connection error. Check your Elastic' +
                          ' Search setting and make sure Elastic Search is' +
                          'running.')
                    sys.exit(0)
                except:
                    print('An expected error: %s' % (sys.exc_info()[0]))
                    sys.exit(0)

            print('The update is completed. %s new records were added.' %
                  added_counter)

    def download(self):

        # Open the url
        try:
            f = urlopen(self.l8_metadata_url)
            if self.file_is_csv(f):
                print("downloading " + self.l8_metadata_url)
                CHUNK = 800 * 1024

                counter = 0
                total_size = self.get_url_file_size(f)
                # Open our local file for writing
                with open('%s/%s' % (self.assests_dir,
                                     self.l8_metadata_filename),
                          "wb") as meta_file:
                    while True:
                        chunk = f.read(CHUNK)
                        if not chunk:
                            break

                        meta_file.write(chunk)
                        counter += 1
                        chunk_sum = float(counter * CHUNK)
                        perct = chunk_sum / total_size
                        print('==> download progress: {:.2%}'.format(perct),
                              end='\r')
                        sys.stdout.flush()

                print('==> Download completed')

                return True
            else:
                print('The URL provided doesn\'t include a CSV file')
                return False

        # handle errors
        except HTTPError, e:
            print("HTTP Error:", e.code, self.l8_metadata_url)
        except URLError, e:
            print("URL Error:", e.reason, self.l8_metadata_url)

        return False

    def get_url_file_size(self, remote_file):
        """gets filesize of remote file"""

        size = remote_file.headers.get('content-length')
        return float(size)

    def file_is_csv(self, remote_file):
        """Checks whether the file is CSV"""

        if 'csv' in remote_file.headers.get('content-type'):
            return True
        else:
            return False
