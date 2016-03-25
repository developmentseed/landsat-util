# Pansharpened Image Process using Rasterio
# Landsat Util
# License: CC0 1.0 Universal

from __future__ import print_function, division, absolute_import

import sys
import subprocess
from termcolor import colored


class VerbosityMixin(object):
    """
    Verbosity Mixin that generates beautiful stdout outputs.
    """

    verbose = False

    def output(self, value, normal=False, color=None, error=False,
               arrow=False, indent=None):
        """ Handles verbosity of this calls.
        if priority is set to 1, the value is printed

        if class instance verbose is True, the value is printed

        :param value:
            a string representing the message to be printed
        :type value:
            String
        :param normal:
            if set to true the message is always printed, otherwise it is only shown if verbosity is set
        :type normal:
            boolean
        :param color:
            The color of the message, choices: 'red', 'green', 'blue'
        :type normal:
            String
        :param error:
            if set to true the message appears in red
        :type error:
            Boolean
        :param arrow:
            if set to true an arrow appears before the message
        :type arrow:
            Boolean
        :param indent:
            indents the message based on the number provided
        :type indent:
            Boolean

        :returns:
            void
        """

        if error and value and (normal or self.verbose):
            return self._print(value, color='red', indent=indent)

        if self.verbose or normal:
            return self._print(value, color, arrow, indent)

        return

    def subprocess(self, argv):
        """
        Execute subprocess commands with proper ouput.
        This is no longer used in landsat-util

        :param argv:
            A list of subprocess arguments
        :type argv:
            List

        :returns:
            void
        """

        if self.verbose:
            proc = subprocess.Popen(argv, stderr=subprocess.PIPE)
        else:
            proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

        self.output(proc.stderr.read(), error=True)

        return

    def exit(self, message):
        """ outputs an exit message and exits

        :param message:
            The message to be outputed
        :type message:
            String

        :returns:
            void
        """

        self.output(message, normal=True, color="green")
        sys.exit()

    def _print(self, msg, color=None, arrow=False, indent=None):
        """ Print the msg with the color provided. """
        if color:
            msg = colored(msg, color)

        if arrow:
            msg = colored('===> ', 'blue') + msg

        if indent:
            msg = ('     ' * indent) + msg

        print(msg)

        return msg
