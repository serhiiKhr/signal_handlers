import os
import re
from .constants import UNITS

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

def detect_unit_type(unit_str: str) -> str:
    """
    Определяет тип единицы измерения по строке.
    Возвращает: 'm/s²' или 'g'
    """
    if not unit_str:
        raise ValueError("detect_unit_type empty  string error")

    u = unit_str.lower()
    u = u.replace(" ", "")
    u = u.replace("^", "")
    u = u.replace("²", "2")
    u = u.replace("сек", "s")
    u = u.replace(",", ".")

    mps2_patterns = [
        r"м/?с2", r"мс2", r"м/с2", r"m/s2", r"mps2", r"мс-2", r"m/s²", r"м/с²"
    ]

    g_patterns = [
        r"\bg\b", r"\bgforce\b", r"\bg²\b", r"\bg2\b", r"\bг\b", r"g/Hz", r"gperhz", r"g\^2", r"g²"
    ]

    for pattern in mps2_patterns:
        if re.search(pattern, u):
            return UNITS['ACCEL_MS2']

    for pattern in g_patterns:
        if re.search(pattern, u):
            return UNITS['ACCEL_G']

    raise ValueError(f"Cannot detect unit type: {unit_str}")