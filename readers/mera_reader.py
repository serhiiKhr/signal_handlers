import tkinter as tk
import configparser
from tkinter import filedialog
import numpy as np
import os

from .base import BaseReader

class MeraReader(BaseReader):
    label = "MERA файл (.mera)"
    
    def load(self):
        mera_path = filedialog.askopenfilename(filetypes=[("MERA files", "*.mera")])
        return mera_path
    
    def get_file_meta(self, filepath: str):
        if not filepath:
            return None
       
        config = configparser.ConfigParser(strict=False)
        config.read(filepath, encoding='windows-1251')
        return {s: config[s] for s in config.sections() if s != 'MERA'}
    
    def get_channels(self, filepath):
        meta = self.get_file_meta(filepath=filepath)
        return meta.keys()
    
    def read_channel(self, filepath, channel):
        # global mera_path, parameters
        
        if not filepath:
            return None
       
        meta = self.get_file_meta(filepath=filepath)
        y_format = meta.get("YFormat", "I2")
        step = float(meta.get("Step", 1.0))
        freq = float(meta.get("Freq", 1.0 / step))
        k0 = float(meta.get("k0", 0))
        k1 = float(meta.get("k1", 1))
        polyTX = int(meta.get("PolyTX", 0))
        y_units = meta.get("YUnits", "В").lower()
        
        dtype_map = {
            "I1": np.int8, "UI1": np.uint8,
            "I2": np.int16, "UI2": np.uint16,
            "I4": np.int32, "I8": np.int64,
            "R4": np.float32, "R8": np.float64
        }
        dat_path = os.path.join(os.path.dirname(filepath), channel + ".dat")
        dtype = dtype_map.get(y_format.upper(), np.int16)
        data = np.fromfile(dat_path, dtype=dtype)
        
        if polyTX == 0:
            data = k1 * (data - k0)
        else:
            data = k1 * data + k0
    
        return data