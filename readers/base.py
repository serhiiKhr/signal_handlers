import pandas as pd

from abc import ABC, abstractmethod
class BaseReader(ABC):
    @staticmethod
    def load():
        pass
    
    @abstractmethod
    def get_channels(self, filepath: str):
        pass
    
    @abstractmethod
    def read_channel(self, filepath: str, channel: str):
        pass
    
    def ensure_series(self, data):
        if not isinstance(data, pd.Series):
            data = pd.Series(data)
        return data
    
    def slice_signal(self, data, sampling_rate: float, start_time: float, end_time: float):
        if start_time is None:
            start_time = 0.0
        if end_time is None:
            end_time = len(data) / sampling_rate
            
        if end_time <= start_time or end_time <= 0:
            return data
        
        _data = self.ensure_series(data)
            
        start_idx = int(start_time * sampling_rate)
        end_idx = int(end_time * sampling_rate)
        # return data.loc[start_idx:end_idx]
        return _data.iloc[start_idx:end_idx]
        