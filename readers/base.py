from abc import ABC, abstractmethod
class BaseReader(ABC):
    @abstractmethod
    def load(self):
        pass
    
    @abstractmethod
    def get_channels(self, filepath: str):
        pass
    
    @abstractmethod
    def read_channel(self, filepath: str, channel: str):
        pass