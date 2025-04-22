from abc import ABC, abstractmethod
class BaseReader(ABC):
    @abstractmethod
    def read(self, filepath: str):
        pass