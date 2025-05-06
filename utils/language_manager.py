import json
import os

from decorators import singleton

from .helpers import deep_get

DEFAULT_LANGUAGE = 'uk'

base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, '..', 'translations.json')

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
