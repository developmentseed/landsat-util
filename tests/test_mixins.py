# Landsat Util
# License: CC0 1.0 Universal

"""Tests for mixins"""

from __future__ import absolute_import

import sys
import unittest

try:
    from io import StringIO
except:
    from cStringIO import StringIO

from contextlib import contextmanager

from landsat.mixins import VerbosityMixin


# Capture function is taken from
# http://schinckel.net/2013/04/15/capture-and-test-sys.stdout-sys.stderr-in-unittest.testcase/
@contextmanager
def capture(command, *args, **kwargs):
    out, sys.stdout = sys.stdout, StringIO()
    command(*args, **kwargs)
    sys.stdout.seek(0)
    yield sys.stdout.read()
    sys.stdout = out


class TestMixins(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.v = VerbosityMixin()

    def test_output(self):
        # just a value
        with capture(self.v.output, u'this is a test') as output:
            self.assertEquals("", output)

        # value as normal
        with capture(self.v.output, u'this is a test', normal=True) as output:
            self.assertEquals("this is a test\n", output)

        # value as normal with color
        with capture(self.v.output, u'this is a test', normal=True, color='blue') as output:
            self.assertEquals("\x1b[34mthis is a test\x1b[0m\n", output)

        # value as error
        with capture(self.v.output, u'this is a test', normal=True, error=True) as output:
            self.assertEquals("\x1b[31mthis is a test\x1b[0m\n", output)

        # value with arrow
        with capture(self.v.output, u'this is a test', normal=True, arrow=True) as output:
            self.assertEquals("\x1b[34m===> \x1b[0mthis is a test\n", output)

        # value with indent
        with capture(self.v.output, u'this is a test', normal=True, indent=1) as output:
            self.assertEquals("     this is a test\n", output)

    def test_exit(self):
        with self.assertRaises(SystemExit):
            with capture(self.v.exit, u'exit test') as output:
                self.assertEquals('exit test', output)

    def test_print(self):
        # message in blue with arrow
        with capture(self.v._print, msg=u'this is a test', color='blue', arrow=True) as output:
            self.assertEquals("\x1b[34m===> \x1b[0m\x1b[34mthis is a test\x1b[0m\n", output)

        # just a message
        with capture(self.v._print, msg=u'this is a test') as output:
            self.assertEquals("this is a test\n", output)

        # message with color and indent
        with capture(self.v._print, msg=u'this is a test', color='blue', indent=1) as output:
            self.assertEquals("     \x1b[34mthis is a test\x1b[0m\n", output)


if __name__ == '__main__':
    unittest.main()
