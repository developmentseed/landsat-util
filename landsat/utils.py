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
    """
    Captures a subprocess stdout.

    :Usage:
        >>> with Capturing():
        ...     subprocess(args)
    """
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout


class timer(object):
    """
    A timer class.

    :Usage:
        >>> with timer():
        ...     your code
    """
    def __enter__(self):
        self.start = time.time()

    def __exit__(self, type, value, traceback):
        self.end = time.time()
        print 'Time spent : {0:.2f} seconds'.format((self.end - self.start))


def exit(message, code=0):
    """ output a message to stdout and terminates the process.

    :param message:
        Message to be outputed.
    :type message:
        String
    :param code:
        The termination code. Default is 0
    :type code:
        int

    :returns:
        void
    """

    v = VerbosityMixin()
    if code == 0:
        v.output(message, normal=True, arrow=True)
        v.output('Done!', normal=True, arrow=True)
    else:
        v.output(message, normal=True, error=True)
    sys.exit(code)


def create_paired_list(value):
    """ Create a list of paired items from a string.

    :param value:
        the format must be 003,003,004,004 (commas with no space)
    :type value:
        String

    :returns:
        List

    :example:
        >>> create_paired_list('003,003,004,004')
        [['003','003'], ['004', '004']]

    """

    if isinstance(value, list):
        value = ",".join(value)

    array = re.split('\D+', value)

    # Make sure the elements in the list are even and pairable
    if len(array) % 2 == 0:
        new_array = [list(array[i:i + 2]) for i in range(0, len(array), 2)]
        return new_array
    else:
        raise ValueError('The string should include pairs and be formated. '
                         'The format must be 003,003,004,004 (commas with '
                         'no space)')


def check_create_folder(folder_path):
    """ Check whether a folder exists, if not the folder is created.

    :param folder_path:
        Path to the folder
    :type folder_path:
        String

    :returns:
        (String) the path to the folder
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    return folder_path


def get_file(path):
    """ Separate the name of the file or folder from the path and return it.

    :param path:
        Path to the folder
    :type path:
        String

    :returns:
        (String) the filename

    :example:
        >>> get_file('/path/to/file.jpg')
        'file.jpg'
    """
    return os.path.basename(path)


def get_filename(path):
    """ Return the filename without extension.

    :param path:
        Path to the folder
    :type path:
        String

    :returns:
        (String) the filename without extension

    :example:
        >>> get_filename('/path/to/file.jpg')
        'file'
    """
    return os.path.splitext(get_file(path))[0]


def three_digit(number):
    """ Add 0s to inputs that their length is less than 3.

    :param number:
        The number to convert
    :type number:
        int

    :returns:
        String

    :example:
        >>> three_digit(1)
        '001'
    """
    number = str(number)
    if len(number) == 1:
        return u'00%s' % number
    elif len(number) == 2:
        return u'0%s' % number
    else:
        return number


def georgian_day(date):
    """ Returns the number of days passed since the start of the year.

    :param date:
        The string date with this format %m/%d/%Y
    :type date:
        String

    :returns:
        int

    :example:
        >>> georgian_day('05/1/2015')
        121
    """
    try:
        fmt = '%m/%d/%Y'
        return datetime.strptime(date, fmt).timetuple().tm_yday
    except (ValueError, TypeError):
        return 0


def year(date):
    """ Returns the year.

    :param date:
        The string date with this format %m/%d/%Y
    :type date:
        String

    :returns:
        int

    :example:
        >>> year('05/1/2015')
        2015
    """
    try:
        fmt = '%m/%d/%Y'
        return datetime.strptime(date, fmt).timetuple().tm_year
    except ValueError:
        return 0


def reformat_date(date, new_fmt='%Y-%m-%d'):
    """ Returns reformated date.

    :param date:
        The string date with this format %m/%d/%Y
    :type date:
        String
    :param new_fmt:
        date format string. Default is '%Y-%m-%d'
    :type date:
        String

    :returns:
        int

    :example:
        >>> reformat_date('05/1/2015', '%d/%m/%Y')
        '1/05/2015'
    """
    try:
        if isinstance(date, datetime):
            return date.strftime(new_fmt)
        else:
            fmt = '%m/%d/%Y'
            return datetime.strptime(date, fmt).strftime(new_fmt)
    except ValueError:
        return date


def convert_to_integer_list(value):
    """ Converts a comma separate string to a list

    :param value:
        the format must be 003,003,004,004 (commas with no space)
    :type value:
        String

    :returns:
        List

    :example:
        >>> convert_to_integer_list('003,003,004,004')
        ['003', '003', '004', '004']

    """
    if isinstance(value, list) or value is None:
        return value
    else:
        s = re.findall('(10|11|QA|[0-9])', value)
        for k, v in enumerate(s):
            try:
                s[k] = int(v)
            except ValueError:
                pass
        return s
