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
    
    def slice_signal(self, data, sampling_rate: float, start_time: float, end_time: float):
        if start_time is None:
            start_time = 0.0
        if end_time is None:
            end_time = len(data) / sampling_rate
            
        if end_time <= start_time or end_time <= 0:
            return data
            
        start_idx = int(start_time * sampling_rate)
        end_idx = int(end_time * sampling_rate)
        return data[start_idx:end_idx]
        