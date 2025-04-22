from abc import ABC, abstractmethod
class BaseAnalyzer:
    @abstractmethod
    def analyze(self, sirgnal, **kwargs):
        pass