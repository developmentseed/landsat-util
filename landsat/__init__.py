import settings
import sys

if not settings.DEBUG:
    sys.tracebacklimit = 0

__version__ = '0.5.0'
