import numpy as np
from scipy.signal import butter, filtfilt
from abc import ABC, abstractmethod

from .base import BaseAnalyzer


class Filter(BaseAnalyzer):
    def __init__(self, lowcut=None, highcut=None, order=4):
        """
        :param sampling_rate: Частота дискретизации сигнала
        :param lowcut: Нижняя граница фильтрации (None — не использовать)
        :param highcut: Верхняя граница фильтрации (None — не использовать)
        :param order: Порядок фильтра
        """
        self.lowcut = lowcut
        self.highcut = highcut
        self.order = order

    def _butter_filter(self, data, sampling_rate):
        nyq = 0.5 * sampling_rate
        if self.lowcut and self.highcut:
            btype = 'band'
            low = self.lowcut / nyq
            high = self.highcut / nyq
            b, a = butter(self.order, [low, high], btype=btype)
        elif self.lowcut:
            btype = 'high'
            b, a = butter(self.order, self.lowcut / nyq, btype=btype)
        elif self.highcut:
            btype = 'low'
            b, a = butter(self.order, self.highcut / nyq, btype=btype)
        else:
            return data  # Фильтр не применяется
        return filtfilt(b, a, data)

    def analyze(self, signal, **kwargs):
        sampling_rate = kwargs.get('sampling_rate')
        if sampling_rate is None:
            raise ValueError("sampling_rate is required")
        
        filtered = self._butter_filter(signal, sampling_rate)
        return filtered