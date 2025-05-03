import tkinter as tk
from tkinter import ttk

from .base import BaseSettingsDialog

class STFTSettings(BaseSettingsDialog):
    def __init__(self):
        super().__init__()
        self.window_value = "hann"
        self.nperseg_value = 4096

    def get_title(self):
        return "Налаштування STFT"

    def build_ui(self, win):
        ttk.Label(win, text="Вікно FFT:").grid(column=0, row=0, sticky='e', padx=10, pady=5)
        self.window_cb = ttk.Combobox(win, values=["hann", "hamming", "blackman", "boxcar"], state="readonly")
        self.window_cb.set(self.window_value)
        self.window_cb.grid(column=1, row=0, padx=10, pady=5)

        ttk.Label(win, text="Кількість ліній спектру:").grid(column=0, row=1, sticky='e', padx=10, pady=5)
        self.nperseg_cb = ttk.Combobox(win, values=[2**i for i in range(7, 14)], state="readonly")
        self.nperseg_cb.set(self.nperseg_value)
        self.nperseg_cb.grid(column=1, row=1, padx=10, pady=5)

    def collect_settings(self):
        self.window_value = self.window_cb.get()
        self.nperseg_value = int(self.nperseg_cb.get())
        self._result = {
            "window": self.window_value,
            "nperseg": self.nperseg_value
        }

    def get_row(self):
        return 2

    