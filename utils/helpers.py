import os

def deep_get(d, keys, default=None):
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        elif isinstance(d, list) and isinstance(key, int):
            if 0 <= key < len(d):
                d = d[key]
            else:
                return default
        elif hasattr(d, key):
            d = getattr(d, key)
        else:
            return default
    return d

def group_by(data, by):
    groupped = {}
    
    values = data.values() if isinstance(data, dict) else data
    for value in values:
        prop_by = deep_get(value, [by], '')
        
        if prop_by:
            if prop_by in groupped and isinstance(groupped[prop_by], list):
                groupped[prop_by].append(value)
            else:
                groupped[prop_by] = [value]
                
    return groupped

def find_index(data, cb):
    values = data.values() if isinstance(data, dict) else data
    for i, val in enumerate(values):
        if cb(val):
            return i
    return -1

def get_filename_without_extension(path: str = ''):
    return os.path.splitext(os.path.basename(path))[0]

def get_file_path(full_path: str) -> str:
    return os.path.dirname(full_path)

def ensure_path_from_parts(parts: list[str]) -> str:
    path = os.path.join(*parts)
    os.makedirs(path, exist_ok=True)
    return path