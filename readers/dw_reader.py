from tkinter import filedialog
import logging
import dwdatareader as dw

logger = logging.getLogger(__name__)

dw.encoding = 'utf-8'


from .base import BaseReader

from utils import LanguageManager
from utils.helpers import deep_get
from utils.constants import DEWESOFT

lang = LanguageManager()
extensions = ', '.join(DEWESOFT.extensions)
class DWReader(BaseReader):
    id = DEWESOFT.id
    label = lang.get('dewesoft.label', extensions=extensions)
    
    def __init__(self, filepath: str = ''):
        self.filepath = filepath
        
    @staticmethod 
    def load():
        mera_path = filedialog.askopenfilename(filetypes=[(DWReader.label, extensions)])
        return mera_path
    
    def get_sampling_rate(self, ch_name: str = ''):
        with dw.open(self.filepath) as f:
            return f.info.sample_rate
        
    def get_channels(self):
        with dw.open(self.filepath) as f:
           
            return [ch.name for ch in f.channels]
        
    def get_y_units(self, channel: str = '') -> str:
        with dw.open(self.filepath) as f:
            for ch in f.channels:
                if channel == ch.name: 
                    return deep_get(ch, ['unit'], '')
      
        return ''
    
    def read_channel(self, channel: str = ''):
        with dw.open(self.filepath) as f:
            for ch in f.channels:
                if channel == ch.name:
                    dataframe = ch.dataframe() 
                    return dataframe[channel]
        
        return None
 
    def get_signal_length(self, channel: str):
        with dw.open(self.filepath) as f:
            for ch in f.channels:
                if channel == ch.name:
                    number_of_samples = ch.number_of_samples
                    sampling_rate = self.get_sampling_rate(ch_name=channel)
                    length = number_of_samples / sampling_rate
                    return length
      
        return None
    

    
