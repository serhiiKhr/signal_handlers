import tkinter as tk
from tkinter import ttk

from .base import BaseSettingsDialog

from utils.language_manager import LanguageManager
from utils.constants import (
    WINDOWS, 
    NPERSEGS,
    PSD_SCALINGS,
    DEFAULT_WINDOW,
    DEFAULT_NPERSEG,
    DEFAULT_MIN_FREQ,
    DEFAULT_MAX_FREQ,
    DEFAULT_OVERLAAP_PERCENT,
    DEFAULT_MIN_DISPLAY_FREQ,
    DEFAULT_PSD_SCALING
)


class PSDSettings(BaseSettingsDialog):
    def __init__(self, data=None):
        super().__init__()
        self.lang = LanguageManager()
        
        self.window_value = (data or {}).get('window', DEFAULT_WINDOW)
        self.nperseg_value = (data or {}).get('nperseg', DEFAULT_NPERSEG)
        self.min_freq_value = (data or {}).get('min_freq', DEFAULT_MIN_FREQ)
        self.max_freq_value = (data or {}).get('max_freq', DEFAULT_MAX_FREQ)
        self.overlap_percent_value = (data or {}).get('overlap_percent', DEFAULT_OVERLAAP_PERCENT)
        self.scaling_value = (data or {}).get('scaling', DEFAULT_PSD_SCALING)
        # self.min_display_freq_value = (data or {}).get('min_display_freq', DEFAULT_MIN_DISPLAY_FREQ)
        
    def get_title(self):
        return self.lang.get("psd.settings")
    
    
    def build_ui(self, win):
        ttk.Label(win, text=self.lang.get("psd.window")).grid(column=0, row=0, sticky='e', padx=10, pady=5)
        self.rows = 0
        self.window_cb = ttk.Combobox(win, values=WINDOWS, state="readonly")
        self.window_cb.set(self.window_value)
        self.window_cb.grid(column=1, row=self.rows, padx=10, pady=5)
        self.rows += 1

        ttk.Label(win, text=self.lang.get("psd.nperseg")).grid(column=0, row=1, sticky='e', padx=10, pady=5)
        self.nperseg_cb = ttk.Combobox(win, values=NPERSEGS, state="readonly")
        self.nperseg_cb.set(self.nperseg_value)
        self.nperseg_cb.grid(column=1, row=self.rows, padx=10, pady=5)
        self.rows += 1
        
        ttk.Label(win, text=self.lang.get("psd.min_freq")).grid(row=self.rows, column=0, sticky='e', padx=10, pady=5)
        self.freq_min_entry = ttk.Entry(win)
        self.freq_min_entry.insert(0, str(self.min_freq_value))
        self.freq_min_entry.grid(row=self.rows, column=1, pady=5)
        self.rows += 1

        ttk.Label(win, text=self.lang.get("psd.max_freq")).grid(row=self.rows, column=0, sticky='e', padx=10, pady=5)
        self.freq_max_entry = ttk.Entry(win)
        self.freq_max_entry.insert(0, str(self.max_freq_value))
        self.freq_max_entry.grid(row=self.rows, column=1, pady=5)
        self.rows += 1

        ttk.Label(win, text=self.lang.get("psd.overlap_percent")).grid(row=self.rows, column=0, sticky='e', padx=10, pady=5)
        self.overlap_entry = ttk.Entry(win)
        self.overlap_entry.insert(0, str(self.overlap_percent_value))
        self.overlap_entry.grid(row=self.rows, column=1, pady=5)
        self.rows += 1

        ttk.Label(win, text=self.lang.get("psd.scaling")).grid(row=self.rows, column=0, sticky='e', padx=10, pady=5)
        self.scaling_cb = ttk.Combobox(win, values=PSD_SCALINGS, state="readonly")
        self.scaling_cb.set(self.scaling_value)
        self.scaling_cb.grid(column=1, row=self.rows, padx=10, pady=5)
        self.rows += 1
        
        
    def collect_settings(self):
        self.window_value = self.window_cb.get()
        self.nperseg_value = int(self.nperseg_cb.get())
        self.min_freq_value = float(self.freq_min_entry.get())
        self.max_freq_value = float(self.freq_max_entry.get())
        self.overlap_percent_value = int(self.overlap_entry.get())
        self.scaling_value = self.scaling_cb.get()
        
        return self.get_settings()
    
    def get_settings(self):
        return {
            "window": self.window_value,
            "nperseg": self.nperseg_value,
            "min_freq": self.min_freq_value,
            "max_freq": self.max_freq_value,
            "overlap_percent": self.overlap_percent_value,
            "scaling": self.scaling_value,
        }
        
    def get_rows(self):
        return self.rows