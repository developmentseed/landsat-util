import warnings

import rasterio


def rasterio_decorator(func):
    def wrapped_f(*args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with rasterio.drivers():
                return func(*args, **kwargs)

    return wrapped_f
