# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco
#
# License: CC0 1.0 Universal

import os
import sys
from cStringIO import StringIO
from datetime import datetime


class Capturing(list):

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout


def check_create_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print "%s folder created" % folder_path

    return folder_path


def get_file(path):
    return os.path.basename(path)


def get_filename(path):
    return os.path.splitext(get_file(path))[0]


def three_digit(number):
    number = str(number)
    if len(number) == 1:
        return u'00%s' % number
    elif len(number) == 2:
        return u'0%s' % number


def georgian_day(date):
    fmt = '%m/%d/%Y'
    return datetime.strptime(date, fmt).timetuple().tm_yday


def year(date):
    fmt = '%m/%d/%Y'
    return datetime.strptime(date, fmt).timetuple().tm_year


def reformat_date(date, new_fmt):
    if date:
        fmt = '%m/%d/%Y'
        return datetime.strptime(date, fmt).strftime(new_fmt)
    else:
        return None
