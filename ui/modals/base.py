import tkinter as tk
from tkinter import ttk


class BaseSettingsDialog:
    def __init__(self):
        self.settings_win = None
        self._result = None

    def open(self, parent):
        self.settings_win = tk.Toplevel(parent)
        self.settings_win.title(self.get_title())
        self.settings_win.transient(parent)
        self.settings_win.grab_set()
        self.settings_win.resizable(False, False)

        self.build_ui(self.settings_win)

        ttk.Button(self.settings_win, text="OK", command=self._save_and_close).grid(
            column=0, row=self.get_row(), columnspan=2, pady=10
        )

        self.settings_win.wait_window()

    def build_ui(self, win):
        raise NotImplementedError("Метод build_ui должен быть переопределён в подклассе")

    def _save_and_close(self):
        self.collect_settings()
        self.settings_win.destroy()

    def collect_settings(self):
        raise NotImplementedError("Метод collect_settings должен быть переопределён в подклассе")

    def get_settings(self):
        return self._result

    def get_title(self):
        return "Налаштування"

    def get_row(self):
        """Номер строки, на которой заканчивается build_ui, чтобы правильно разместить кнопку OK"""
        raise NotImplementedError("Метод get_row должен быть переопределён в подклассе")