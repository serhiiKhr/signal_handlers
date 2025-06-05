import tkinter as tk
from tkinter import ttk

from .base import BaseSettingsDialog

from utils.language_manager import LanguageManager
from utils.logger import Logger

class TimeframeSettings(BaseSettingsDialog):
    def __init__(self, data=None, timeframes=None):
        super().__init__()
        self.lang = LanguageManager()
        
        self.name = (data or {}).get('name', '')
        self.start = (data or {}).get('start', 0)
        self.end = (data or {}).get('end', 0)
        self.used_names = [n for n in (tf["name"] for tf in (timeframes or [])) if n != self.name]

    def get_title(self):
        return self.lang.get("timeframe.title")

    def build_ui(self, win):
        def only_numbers(text):
            return text == "" or text.replace('.', '', 1).isdigit()
        
        vcmd = (win.register(only_numbers), '%P')  # регистрация функции валидации
        
        container = ttk.Frame(win, padding=10)
        container.grid(sticky="nsew")
        self.rows = 0
        # ttk.Label(container, text="test").grid(column=0, row=self.rows, sticky='w', padx=10, pady=5)
        # self.rows += 1
        
        ttk.Label(container, text=self.lang.get("timeframe.name")).grid(row=self.rows, column=0, sticky='e', padx=10, pady=5)
        self.name_entry = ttk.Entry(container)
        self.name_entry.insert(0, str(self.name))
        self.name_entry.grid(row=self.rows, column=1, pady=5)
        self.rows += 1

        ttk.Label(container, text=self.lang.get("timeframe.start")).grid(row=self.rows, column=0, sticky='e', padx=10, pady=5)
        self.start_entry = ttk.Entry(container, validate='key', validatecommand=vcmd)
        self.start_entry.insert(0, float(self.start))
        self.start_entry.grid(row=self.rows, column=1, pady=5)
        self.rows += 1

        ttk.Label(container, text=self.lang.get("timeframe.end")).grid(row=self.rows, column=0, sticky='e', padx=10, pady=5)
        self.end_entry = ttk.Entry(container, validate='key', validatecommand=vcmd)
        self.end_entry.insert(0, float(self.end))
        self.end_entry.grid(row=self.rows, column=1, pady=5)
        self.rows += 1

    def collect_settings(self):
        self.name = self.name_entry.get()
        self.start = float(self.start_entry.get())
        self.end = float(self.end_entry.get())
        
        self._result = {
            "name": self.name,
            "start": self.start,
            "end": self.end
        }
        
        return self._result
        

    def get_rows(self):
        return self.rows
    
    def get_settings(self):
        return self._result
        
    def is_valid(self, settings):
        required_fields = ['name', 'start', 'end']
        for field in required_fields:
            if field not in settings or settings[field] in (None, '', []):
                # 
                return False, Logger.error(self.lang.get("logger.field_required", field=field))
        
        name = settings.get('name', '').strip()
        try:
            start = float(settings['start'])
            end = float(settings['end'])
        except ValueError:
            return False, Logger.error(self.lang.get("logger.field_must_be_number", field="'start', 'end'"))

        if end < start:
            return False, Logger.error(self.lang.get("logger.a_must_be_more_then_b", a="'end'", b="'start'"))
        
        if name in self.used_names:
            return False, Logger.error(self.lang.get("logger.already_used", value=name))

        return True, "OK"
        
    def validate(self):
        settings = self.collect_settings()
        valid, text = self.is_valid(settings=settings)
        print('text',  text)
        self.ok_button.configure(state='disabled' if not valid else 'enabled')

    def on_change(self):
        self.validate()
        self.name_entry.bind("<KeyRelease>", lambda e: self.validate())
        self.start_entry.bind("<KeyRelease>", lambda e: self.validate())
        self.end_entry.bind("<KeyRelease>", lambda e: self.validate())