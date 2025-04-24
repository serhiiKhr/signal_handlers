from abc import ABC, abstractmethod
class BaseAnalyzer:
    @abstractmethod
    def analyze(self, signal, **kwargs):
        pass