# Pansharpened Image Process using Rasterio
# Landsat Util
# License: CC0 1.0 Universal

import sys
import subprocess
from termcolor import colored


class VerbosityMixin(object):
    """
    Verbosity Mixin that generates beautiful stdout outputs.

    Main method:
    output()
    """

    verbose = False

    def output(self, value, normal=False, color=None, error=False,
               arrow=False, indent=None):
        """ Handles verbosity of this calls.
        if priority is set to 1, the value is printed

        if class instance verbose is True, the value is printed

        @param
        - value: (string) the message to be printed
        - nomral: (boolean) if set to true the message is always printed,
                  otherwise it is only shown if verbosity is set
        - color: (string) The color of the message, choices: 'red', 'green', 'blue'
        - error: (boolean) if set to true the message appears in red
        - arrow: (boolean) if set to true an arrow appears before the message
        - indent: (integer) indents the message based on the number provided
        """

        if error and value and (normal or self.verbose):
            return self._print(value, color='red', indent=indent)

        if self.verbose or normal:
            return self._print(value, color, arrow, indent)

        return

    def subprocess(self, argv):
        """
        Execute subprocess commands with proper ouput
        This is no longer used in landsat-util
        """

        if self.verbose:
            proc = subprocess.Popen(argv, stderr=subprocess.PIPE)
        else:
            proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

        self.output(proc.stderr.read(), error=True)

        return

    def exit(self, message):
        """ Print an exist message and exit """

        self.output(message, normal=True, color="green")
        sys.exit()

    def _print(self, msg, color=None, arrow=False, indent=None):
        """ Print the msg with the color provided """
        if color:
            msg = colored(msg, color)

        if arrow:
            msg = colored('===> ', 'blue') + msg

        if indent:
            msg = ('     ' * indent) + msg

        sys.stdout.write(msg + '\n')

        return msg
