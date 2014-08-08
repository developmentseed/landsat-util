# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco
#
# License: CC0 1.0 Universal

import json

import requests

import settings
from general_helper import three_digit


class Search(object):

    def __init__(self):
        self.api_url = settings.API_URL

    def search(self,
               row_paths=None,
               start_date=None,
               end_date=None,
               cloud_min=None,
               cloud_max=None,
               limit=1):

        search_string = self.query_builder(row_paths,
                                           start_date,
                                           end_date,
                                           cloud_min,
                                           cloud_max)

        # Have to manually build the URI to bypass requests URI encoding
        # The api server doesn't accept encoded URIs
        r = requests.get('%s?search=%s&limit=%s' % (self.api_url,
                                                    search_string,
                                                    limit))

        r_dict = json.loads(r.text)
        result = {}

        if 'error' in r_dict:
            result['status'] = u'error'
            result['code'] = r_dict['error']['code']
            result['message'] = r_dict['error']['message']

        elif 'meta' in r_dict:
            result['status'] = u'SUCCESS'
            result['total'] = r_dict['meta']['results']['total']
            result['limit'] = r_dict['meta']['results']['limit']
            result['total_returned'] = len(r_dict['results'])
            result['results'] = [{'sceneID': i['sceneID'],
                                  'sat_type': u'L8',
                                  'path': three_digit(i['path']),
                                  'row': three_digit(i['row'])}
                                 for i in r_dict['results']]

        return result

    def query_builder(self,
                      row_paths=None,
                      start_date=None,
                      end_date=None,
                      cloud_min=None,
                      cloud_max=None):
        query = []
        rows_paths = []

        if row_paths:
            row_path_array = row_paths.split(',')
            new_array = [tuple(row_path_array[i:i + 2])
                         for i in range(0, len(row_path_array), 2)]
            rows_paths.extend(['(%s)' % self.row_path_builder(i[0], i[1])
                               for i in new_array])

        if start_date and end_date:
            query.append(self.date_range_builder(start_date, end_date))
        elif start_date:
            query.append(self.date_range_builder(start_date, '2100-01-01'))
        elif end_date:
            query.append(self.date_range_builder('2009-01-01', end_date))

        if cloud_min and cloud_max:
            query.append(self.cloud_cover_prct_range_builder(cloud_min,
                                                             cloud_max))
        elif cloud_min:
            query.append(self.cloud_cover_prct_range_builder(cloud_min,
                                                             '100'))
        elif cloud_max:
            query.append(self.cloud_cover_prct_range_builder('0',
                                                             cloud_max))

        search_string = '+AND+'.join(map(str, query))

        if len(search_string) > 0:
            search_string = search_string + '+AND+' + \
                '+OR+'.join(map(str, rows_paths))
        else:
            search_string = '+OR+'.join(map(str, rows_paths))

        return search_string

    def row_path_builder(self, row, path):
        """ Builds row and path query
            Accepts row and path in XXX format, e.g. 003
        """
        return 'row:%s+AND+path:%s' % (row, path)

    def date_range_builder(self, start, end):
        """ Builds date range query
            Accepts start and end date in this format YYYY-MM-DD
        """
        return 'acquisitionDate:[%s+TO+%s]' % (start, end)

    def cloud_cover_prct_range_builder(self, min, max):
        """ Builds cloud cover percentage range query
            Accepts bottom and top range in float, e.g. 1.00
        """
        return 'cloudCoverFull:[%s+TO+%s]' % (min, max)
