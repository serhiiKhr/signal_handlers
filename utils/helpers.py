import os

def deep_get(d, keys, default=None):
    for key in keys:
        if isinstance(d, dict) and key in d:
            d = d[key]
        else:
            return default
    return d


def get_filename_without_extension(path: str = ''):
    return os.path.splitext(os.path.basename(path))[0]