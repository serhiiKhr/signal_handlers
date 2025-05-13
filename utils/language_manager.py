import json
import sys
import os

from decorators import singleton

from .helpers import deep_get

def resource_path(relative_path):
    """ Gets the absolute path to a resource when running from .exe or from source code """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

DEFAULT_LANGUAGE = 'uk'

base_dir = os.path.dirname(os.path.abspath(__file__))
# file_path = os.path.join(base_dir, '..', 'translations.json')
file_path = resource_path("translations.json")

@singleton
class LanguageManager:
    def __init__(self, default_language=DEFAULT_LANGUAGE):
        self.language = default_language
        self.translation = {}
        self.load_translations()
        
    def load_translations(self):
        with open(file_path, 'r', encoding='UTF-8') as file:
            self.translations = json.load(file)
            
    def change_language(self, language):
        if language in self.translation.keys():
            self.language = language
        else:
            print(f'Language {language} not found, using default ({self.language}).')
            self.language = DEFAULT_LANGUAGE
            
    def get(self, key, **kwargs):
        path = [self.language, *key.split('.')]
        text = deep_get(self.translations, path, key)
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, AttributeError):
            return text  # Returns the text as-is if formatting fails
