# Landsat Util
# License: CC0 1.0 Universal

from __future__ import print_function, division, absolute_import

import os
import sys
import time
import re

try:
    from io import StringIO
except ImportError:
    from cStringIO import StringIO

from datetime import datetime

import geocoder

from .mixins import VerbosityMixin


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
        print('Time spent : {0:.2f} seconds'.format((self.end - self.start)))


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


# Geocoding confidence scores, from https://github.com/DenisCarriere/geocoder/blob/master/docs/features/Confidence%20Score.md
geocode_confidences = {
    10: 0.25,
    9: 0.5,
    8: 1.,
    7: 5.,
    6: 7.5,
    5: 10.,
    4: 15.,
    3: 20.,
    2: 25.,
    1: 99999.,
    # 0: unable to locate at all
}


def geocode(address, required_precision_km=1.):
    """ Identifies the coordinates of an address

    :param address:
        the address to be geocoded
    :type value:
        String
    :param required_precision_km:
        the maximum permissible geographic uncertainty for the geocoding
    :type required_precision_km:
        float

    :returns:
        dict

    :example:
        >>> geocode('1600 Pennsylvania Ave NW, Washington, DC 20500')
        {'lat': 38.89767579999999, 'lon': -77.0364827}

    """
    geocoded = geocoder.google(address)
    precision_km = geocode_confidences[geocoded.confidence]

    if precision_km <= required_precision_km:
        (lon, lat) = geocoded.geometry['coordinates']
        return {'lat': lat, 'lon': lon}
    else:
        raise ValueError("Address could not be precisely located")


def convert_to_float_list(value):
    """ Converts a comma separate string to a list

    :param value:
        the format must be 1.2,-3.5 (commas with no space)
    :type value:
        String

    :returns:
        List

    :example:
        >>> convert_to_integer_list('003,003,004,004')
        [1.2, -3.5]

    """
    if isinstance(value, list) or value is None:
        return value
    else:
        s = re.findall('([-+]?\d*\.\d+|\d+|[-+]?\d+)', value)
        for k, v in enumerate(s):
            try:
                s[k] = float(v)
            except ValueError:
                pass
        return s


def adjust_bounding_box(bounds1, bounds2):
    """ If the bounds 2 corners are outside of bounds1, they will be adjusted to bounds1 corners

    @params
    bounds1 - The source bounding box
    bounds2 - The target bounding box that has to be within bounds1

    @return
    A bounding box tuple in (y1, x1, y2, x2) format
    """

    # out of bound check
    # If it is completely outside of target bounds, return target bounds
    if ((bounds2[0] > bounds1[0] and bounds2[2] > bounds1[0]) or
            (bounds2[2] < bounds1[2] and bounds2[2] < bounds1[0])):
        return bounds1

    if ((bounds2[1] < bounds1[1] and bounds2[3] < bounds1[1]) or
            (bounds2[3] > bounds1[3] and bounds2[1] > bounds1[3])):
        return bounds1

    new_bounds = list(bounds2)

    # Adjust Y axis (Longitude)
    if (bounds2[0] > bounds1[0] or bounds2[0] < bounds1[3]):
        new_bounds[0] = bounds1[0]
    if (bounds2[2] < bounds1[2] or bounds2[2] > bounds1[0]):
        new_bounds[2] = bounds1[2]

    # Adjust X axis (Latitude)
    if (bounds2[1] < bounds1[1] or bounds2[1] > bounds1[3]):
        new_bounds[1] = bounds1[1]
    if (bounds2[3] > bounds1[3] or bounds2[3] < bounds1[1]):
        new_bounds[3] = bounds1[3]

    return tuple(new_bounds)


def remove_slash(value):

    assert(isinstance(value, str))
    return re.sub('(^\/|\/$)', '', value)


def url_builder(segments):

    # Only accept list or tuple
    assert((isinstance(segments, list) or isinstance(segments, tuple)))
    return "/".join([remove_slash(s) for s in segments])

