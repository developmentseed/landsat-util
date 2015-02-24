import settings
import sys

if not settings.DEBUG:
    sys.tracebacklimit = 0
