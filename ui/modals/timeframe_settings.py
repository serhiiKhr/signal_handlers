import tkinter as tk
from tkinter import ttk

from .base import BaseSettingsDialog

from utils.language_manager import LanguageManager

class TimeframeSettings(BaseSettingsDialog):
    def __init__(self, data=None):
        super().__init__()
        self.lang = LanguageManager()
        
        self.name = (data or {}).get('name', '')
        self.start = (data or {}).get('start', 0)
        self.end = (data or {}).get('end', None)

    def get_title(self):
        return self.lang.get("stft.settings")

    def build_ui(self, win):
        ttk.Label(win, text=self.lang.get("stft.window")).grid(column=0, row=0, sticky='e', padx=10, pady=5)
        self.rows = 0
        
        ttk.Label(win, text=self.lang.get("stft.min_freq")).grid(row=self.rows, column=0, sticky='e', padx=10, pady=5)
        self.name_entry = ttk.Entry(win)
        self.name_entry.insert(0, str(self.name))
        self.name_entry.grid(row=self.rows, column=1, pady=5)
        self.rows += 1

        ttk.Label(win, text=self.lang.get("stft.max_freq")).grid(row=self.rows, column=0, sticky='e', padx=10, pady=5)
        self.start_entry = ttk.Entry(win)
        self.start_entry.insert(0, str(self.start))
        self.start_entry.grid(row=self.rows, column=1, pady=5)
        self.rows += 1

        ttk.Label(win, text=self.lang.get("stft.overlap_percent")).grid(row=self.rows, column=0, sticky='e', padx=10, pady=5)
        self.end_entry = ttk.Entry(win)
        self.end_entry.insert(0, str(self.end))
        self.end_entry.grid(row=self.rows, column=1, pady=5)
        self.rows += 1

    def collect_settings(self):
        self.name = self.name_entry.get()
        self.start = float(self.start_entry.get())
        self.end = float(self.end_entry.get())
        
        return self.get_settings()
        

    def get_rows(self):
        return self.rows
    
    def get_settings(self):
        return {
            "name": self.name,
            "start": self.start,
            "end": self.end
        }

    