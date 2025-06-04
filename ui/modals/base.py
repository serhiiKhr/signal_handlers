import tkinter as tk
from tkinter import ttk

from utils.language_manager import LanguageManager
from utils.logger import Logger

class BaseSettingsDialog:
    def __init__(self, data=None):
        self.rows = 0
        self.settings_win = None
        self._result = None
        self.data = data or {}
        self.lang = LanguageManager()

    def open(self, parent):
        self.settings_win = tk.Toplevel(parent)
        self.settings_win.title(self.get_title())
        self.settings_win.transient(parent)
        self.settings_win.grab_set()
        self.settings_win.resizable(False, False)

        self.build_ui(self.settings_win)

        self.ok_button = ttk.Button(self.settings_win, text="OK", command=self._save_and_close)
        self.ok_button.grid(
            column=0, row=self.get_rows(), columnspan=2, pady=10
        )
        
        self.on_change()

        self.settings_win.protocol("WM_DELETE_WINDOW", self._on_close)

        self.settings_win.wait_window()

    def _on_close(self):
        self._result = None
        self.settings_win.destroy()
        
    def build_ui(self, win):
        Logger.warning(self.lang.get('logger.must_be_overridden', method="build_ui"))
        return

    def _save_and_close(self):
        self.collect_settings()
        self.settings_win.destroy()

    def collect_settings(self):
        Logger.warning(self.lang.get('logger.must_be_overridden', method="collect_settings"))
        return

    def get_settings(self):
        return self._result

    def get_title(self):
        lang = LanguageManager()
        return lang.get("ui.settings")

    def get_rows(self):
        """The line number where build_ui ends, to correctly position the OK button."""
        Logger.warning(self.lang.get('logger.must_be_overridden', method="get_row"))
        return
    
    def on_change(self):
        pass
    