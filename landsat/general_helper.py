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
    """ Check whether a folder exists, if not the folder is created
    Always return folder_path
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print "%s folder created" % folder_path

    return folder_path


def get_file(path):
    """ Separate the name of the file or folder from the path and return it
    Example: /path/to/file ---> file
    """
    return os.path.basename(path)


def get_filename(path):
    """ Return the filename without extension. e.g. index.html --> index """
    return os.path.splitext(get_file(path))[0]


def three_digit(number):
    """ Add 0s to inputs that their length is less than 3.
    For example: 1 --> 001 | 02 --> 020 | st --> 0st
    """
    number = str(number)
    if len(number) == 1:
        return u'00%s' % number
    elif len(number) == 2:
        return u'0%s' % number
    else:
        return number


def georgian_day(date):
    """ Returns the number of days passed since the start of the year
    Accepted format: %m/%d/%Y
    """
    try:
        fmt = '%m/%d/%Y'
        return datetime.strptime(date, fmt).timetuple().tm_yday
    except (ValueError, TypeError):
        return 0


def year(date):
    """ Returns the year
    Accepted format: %m/%d/%Y
    """
    try:
        fmt = '%m/%d/%Y'
        return datetime.strptime(date, fmt).timetuple().tm_year
    except ValueError:
        return 0


def reformat_date(date, new_fmt):
    """ Return reformated date. Example: 01/28/2014 & %d/%m/%Y -> 28/01/2014
    Accepted date format: %m/%d/%Y
    """
    try:
        fmt = '%m/%d/%Y'
        return datetime.strptime(date, fmt).strftime(new_fmt)
    except ValueError:
        return date
