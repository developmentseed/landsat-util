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
from general_helper import three_digit, create_paired_list


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
        """
        The main method of Search class. It searches the DevSeed Landsat API

        Returns python dictionary

        Arguments:
            row_paths -- A string in this format: "003,003,004,004". Must be in pairs
            start_date -- date string. format: YYYY-MM-DD
            end_date -- date string. format: YYYY-MM-DD
            cloud_min -- float specifying the minimum percentage. e.g. 4.3
            cloud_max -- float specifying the maximum percentage. e.g. 78.9
            limit -- integer specigying the maximum results return.

        Example:

            search('003,003', '2014-01-01', '2014-06-01')

            will return:

            {
                'status': u'SUCCESS',
                'total_returned': 1,
                'total': 1,
                'limit': 1
                'results': [
                    {
                        'sat_type': u'L8',
                        'sceneID': u'LC80030032014142LGN00',
                        'date': u'2014-05-22',
                        'path': u'003',
                        'thumbnail': u'http://earthexplorer.usgs.gov/browse/landsat_8/2014/003/003/LC80030032014142LGN00.jpg',
                        'cloud': 33.36,
                        'row': u'003
                    }
                ]
            }
        """

        search_string = self._query_builder(row_paths,
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
                                  'row': three_digit(i['row']),
                                  'thumbnail': i['browseURL'],
                                  'date': i['acquisitionDate'],
                                  'cloud': i['cloudCoverFull']}
                                 for i in r_dict['results']]

        return result

    def _query_builder(self,
                       row_paths=None,
                       start_date=None,
                       end_date=None,
                       cloud_min=None,
                       cloud_max=None):
        """ Builds the proper search syntax (query) for Landsat API """

        query = []
        rows_paths = []

        # Coverting rows and paths to paired list
        try:
            new_array = create_paired_list(row_paths)

            rows_paths.extend(['(%s)' % self._row_path_builder(i[0], i[1])
                               for i in new_array])
        except ValueError:
            return ''

        if start_date and end_date:
            query.append(self._date_range_builder(start_date, end_date))
        elif start_date:
            query.append(self._date_range_builder(start_date, '2100-01-01'))
        elif end_date:
            query.append(self._date_range_builder('2009-01-01', end_date))

        if cloud_min and cloud_max:
            query.append(self._cloud_cover_prct_range_builder(cloud_min,
                                                              cloud_max))
        elif cloud_min:
            query.append(self._cloud_cover_prct_range_builder(cloud_min,
                                                              '100'))
        elif cloud_max:
            query.append(self._cloud_cover_prct_range_builder('-1',
                                                              cloud_max))

        search_string = '+AND+'.join(map(str, query))

        if len(search_string) > 0:
            search_string = search_string + '+AND+(' + \
                '+OR+'.join(map(str, rows_paths)) +')'
        else:
            search_string = '+OR+'.join(map(str, rows_paths))

        return search_string

    def _row_path_builder(self, path, row):
        """ Builds row and path query
            Accepts row and path in XXX format, e.g. 003
        """
        return 'row:%s+AND+path:%s' % (row, path)

    def _date_range_builder(self, start, end):
        """ Builds date range query
            Accepts start and end date in this format YYYY-MM-DD
        """
        return 'acquisitionDate:[%s+TO+%s]' % (start, end)

    def _cloud_cover_prct_range_builder(self, min, max):
        """ Builds cloud cover percentage range query
            Accepts bottom and top range in float, e.g. 1.00
        """
        return 'cloudCoverFull:[%s+TO+%s]' % (min, max)
