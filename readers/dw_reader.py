from tkinter import filedialog

from .base import BaseReader

class DWReader(BaseReader):
    label = 'Dewesoft файл (.d7d)'
    
    
    def __init__(self, filepath: str = ''):
        self.filepath = filepath
        
    @staticmethod 
    def load():
        mera_path = filedialog.askopenfilename(filetypes=[("Dewesoft files", "*.d7d")])
        return mera_path
    
    
