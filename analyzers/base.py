from abc import ABC, abstractmethod
class BaseAnalyzer:
    @abstractmethod
    def analyze(self, signal, **kwargs):
        pass
    
    @abstractmethod
    def frame_signal(self, signal, min_freq=None, max_freq=None):
        pass