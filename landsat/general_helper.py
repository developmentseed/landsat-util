# Landsat Util
# License: CC0 1.0 Universal

import os
import sys
import time
import re
from cStringIO import StringIO
from datetime import datetime

from mixins import VerbosityMixin


class Capturing(list):
    """ Captures a subprocess stdout """
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout


class timer(object):
    """
    A time class

    Usage:
        with timer():
            your code
    """
    def __enter__(self):
        self.start = time.time()

    def __exit__(self, type, value, traceback):
        self.end = time.time()
        print 'Time spent : {0:.2f} seconds'.format((self.end - self.start))


def exit(message):
    v = VerbosityMixin()
    v.output(message, normal=True, color="green")
    sys.exit()


def create_paired_list(i):
    """ Create a list of paired items from a string

    Arguments:
        i - the format must be 003,003,004,004 (commas with no space)

    Returns:
        [['003','003'], ['004', '004']]
    """

    if isinstance(i, str):
        array = i.split(',')
    elif isinstance(i, list):
        # Make sure it is not already paired
        if isinstance(i[0], list) or isinstance(i[0], tuple):
            return i
        else:
            array = i
    else:
        return i

    # Make sure the elements in the list are even and pairable
    if len(array) % 2 == 0:
        new_array = [list(array[i:i + 2])
                     for i in range(0, len(array), 2)]
        return new_array
    else:
        raise ValueError('The string should include pairs and be formated. '
                         'The format must be 003,003,004,004 (commas with '
                         'no space)')


def check_create_folder(folder_path):
    """ Check whether a folder exists, if not the folder is created
    Always return folder_path
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

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


def reformat_date(date, new_fmt='%Y-%m-%d'):
    """ Return reformated date. Example: 01/28/2014 & %d/%m/%Y -> 28/01/2014
    Accepted date format: %m/%d/%Y
    """
    try:
        if type(date) is datetime:
            return date.strftime(new_fmt)
        else:
            fmt = '%m/%d/%Y'
            return datetime.strptime(date, fmt).strftime(new_fmt)
    except ValueError:
        return date


def convert_to_integer_list(value):
    """ convert a comma separate string to a list where all values are integers """

    if value:
        new_list = re.findall('[0-9]', value)
        return new_list if new_list else None
    else:
        return value
