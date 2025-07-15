from scipy.signal.windows import hann, blackmanharris, boxcar, hamming, bartlett, flattop, kaiser
from scipy.signal import welch
import numpy as np

from .base import BaseAnalyzer

from utils import ANALYSIS, LanguageManager
from utils.constants import (
    DEFAULT_WINDOW,
    DEFAULT_NPERSEG,
    DEFAULT_MIN_FREQ,
    DEFAULT_MAX_FREQ,
    DEFAULT_OVERLAAP_PERCENT,
    DEFAULT_MIN_DISPLAY_FREQ,
    DEFAULT_PSD_SCALING,
    UNITS,
    G
)


class PSD(BaseAnalyzer):
    id: str = ANALYSIS['PSD']
    label: str = LanguageManager().get('psd.label')
    
    def __init__(
            self,
            nperseg: int = DEFAULT_WINDOW,
            window: str = DEFAULT_NPERSEG,
            min_freq: float = DEFAULT_MIN_FREQ, 
            max_freq: float = DEFAULT_MAX_FREQ, 
            overlap_percent: float = DEFAULT_OVERLAAP_PERCENT,
            min_display_freq: float = DEFAULT_MIN_DISPLAY_FREQ,
            scaling: str = DEFAULT_PSD_SCALING
        ):
        self.nperseg = nperseg
        self.window = window
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.overlap_percent = overlap_percent
        self.scaling = scaling
        
        
    def frame_signal(self, signal, min_freq=None, max_freq=None):
        if min_freq is None and max_freq is None:
            return signal
        
        frequencies, psd_values = signal 
        freq_mask = np.ones_like(frequencies, dtype=bool)

        if min_freq is not None:
            freq_mask &= frequencies >= min_freq
        if max_freq is not None:
            freq_mask &= frequencies <= max_freq

        filtered_frequencies = frequencies[freq_mask]
        filtered_psd = psd_values[freq_mask]

        return filtered_frequencies, filtered_psd
        
        
    def analyze(self, signal, **kwargs):
        sampling_rate = kwargs.get('sampling_rate')
        # min_freq = kwargs.get('min_freq') or self.min_freq 
        # max_freq = kwargs.get('max_freq') or self.max_freq 
        
        _nperseg = self.nperseg
        if len(signal) < self.nperseg:
            _nperseg = len(signal)
            
        noverlap = 0
        if self.overlap_percent is not None and isinstance(self.overlap_percent, (float, int)) and self.overlap_percent > 0:
            noverlap = int((self.overlap_percent / 100) * _nperseg)
        
        if self.window == 'hann':
            window = hann(_nperseg)
        elif self.window == 'blackman':
            window = blackmanharris(_nperseg)
        elif self.window == 'boxcar':
            window = boxcar(_nperseg)
        elif self.window == 'hamming':
            window = hamming(_nperseg)
        elif self.window == 'bartlett':
            window = bartlett(_nperseg)
        elif self.window == 'flattop':
            window = flattop(_nperseg)
        elif self.window == 'kaiser':
            window = kaiser(_nperseg, beta=14)
        else:
            window = hann(_nperseg)
                    
        frequencies, psd = welch(
            signal,
            fs=sampling_rate,
            window=window,
            nperseg=_nperseg,
            noverlap=noverlap,
            scaling=self.scaling
        )
        
        return self.frame_signal((frequencies, psd), min_freq=self.min_freq, max_freq=self.max_freq)
    
    def convert_psd_to_g(self, psd: np.ndarray, unit_type: str) -> np.ndarray:
        """
        Преобразует PSD в g²/Hz, если исходный сигнал в м/с².
        Если уже в g — возвращает без изменений.
        """
        if unit_type == UNITS['ACCEL_MS2']:
            
            return psd / (G ** 2)
        elif unit_type == UNITS["ACCEL_G"]:
            return psd
        else:
            raise ValueError(f"Неизвестный тип единицы: {unit_type}")
        