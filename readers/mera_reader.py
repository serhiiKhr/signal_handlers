import tkinter as tk
import configparser
from tkinter import filedialog
import numpy as np
import os

from .base import BaseReader

from utils.helpers import deep_get
from utils.language_manager import LanguageManager
from utils.constants import MERA

lang = LanguageManager()
extensions = ', '.join(MERA.extensions)

class MeraReader(BaseReader):
    label = lang.get('mera.label', extensions=extensions)
    
    def __init__(self, filepath: str = ''):
        self.filepath = filepath
    
    @staticmethod
    def load():
        mera_path = filedialog.askopenfilename(filetypes=[(MeraReader.label, extensions)])
        return mera_path
    
    def get_sampling_rate(self, ch_name: str = ''):
        meta = self.get_file_meta()
        return float(deep_get(meta, [ch_name, 'freq'], 0))
    
    def get_file_meta(self):
        if not self.filepath:
            return None
       
        config = configparser.ConfigParser(strict=False)
        config.read(self.filepath, encoding='windows-1251')
        return {section: dict(config[section]) for section in config.sections()}
    
    def get_channels(self):
        meta = self.get_file_meta()
        
        return [name for name in meta.keys() if name.lower() != 'mera']
    
    def get_y_units(self, channel: str = '') -> str:
        if not channel:
            return ''
        
        meta = self.get_file_meta()
        return deep_get(meta, [channel, 'yunits'], '')

    
    def read_channel(self, channel):
        # global mera_path, parameters
        
        if not self.filepath:
            return None
       
        meta = self.get_file_meta()
        y_format = meta.get("YFormat", "I2")
        freq = deep_get(meta, [channel, 'freq'], 0)
        step = float(meta.get("Step", 1.0))

        k0 = float(meta.get("k0", 0))
        k1 = float(meta.get("k1", 1))
        polyTX = int(meta.get("PolyTX", 0))

        dtype_map = {
            "I1": np.int8, "UI1": np.uint8,
            "I2": np.int16, "UI2": np.uint16,
            "I4": np.int32, "I8": np.int64,
            "R4": np.float32, "R8": np.float64
        }
        dat_path = os.path.join(os.path.dirname(self.filepath), channel + ".dat")
        dtype = dtype_map.get(y_format.upper(), np.int16)
        data = np.fromfile(dat_path, dtype=dtype)
        
        if polyTX == 0:
            data = k1 * (data - k0)
        else:
            data = k1 * data + k0
    
        return data