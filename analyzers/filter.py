import numpy as np
from scipy.signal import butter, filtfilt
from abc import ABC, abstractmethod
from utils import Logger, LanguageManager

from .base import BaseAnalyzer


class Filter(BaseAnalyzer):
    def __init__(self, lowcut=None, highcut=None, order=4):
        """
        :param sampling_rate: Sampling rate of the signal  
        :param lowcut: Lower cutoff frequency for filtering (None — do not apply)  
        :param highcut: Upper cutoff frequency for filtering (None — do not apply)  
        :param order: Filter order  
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
            return data  # No filtering is performed
        return filtfilt(b, a, data)

    def analyze(self, signal, **kwargs):
        sampling_rate = kwargs.get('sampling_rate')
        if sampling_rate is None:
            lang = LanguageManager()
            Logger.error(lang.get("logger.field_required", field="sampling_rate"))
            return None
        
        filtered = self._butter_filter(signal, sampling_rate)
        return filtered