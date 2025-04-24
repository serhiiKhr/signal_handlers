import numpy
from scipy.signal.windows import hann, blackmanharris
from scipy.signal import stft

from utils import compare_window

from .base import BaseAnalyzer

class STFT(BaseAnalyzer):
    label = "STFT анализ"
    def __init__(self,
                 nperseg: int = 1,
                 window: str = 'hann',
                 min_freq: float = 5.0, 
                 max_freq: float = 2000.0, 
                 overlap_percent: float = 0.0,
                 min_display_freq: float = 100.0
                 ):
        self.nperseg = nperseg * 2
        self.window = window
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.overlap_percent = overlap_percent
        # todo: add checking, if min_display_freq above than max freq value
        # self.min_display_freq = 5000 # min_display_freq
        self.min_display_freq = min_display_freq
        pass
    
    
    def analyze(self, signal, sampling_rate):
        if compare_window('HANNING', self.window):
            window = hann(self.nperseg)
        elif compare_window('BLACKMANHARRIS', self.window):
            window = blackmanharris(self.nperseg)
        else:
            window = hann(self.nperseg)
                        
        noverlap = 0
        if self.overlap_percent is not None and isinstance(self.overlap_percent, (float, int)) and self.overlap_percent > 0:
            noverlap = int((self.overlap_percent / 100) * self.nperseg)

        frequencies, time, spectr = stft(
            signal,
            fs=sampling_rate,
            window=window,
            nperseg=self.nperseg,
            noverlap=noverlap,
            boundary='zeros'
        )
        window_correction = numpy.sum(window) / self.nperseg
        corrected_spectr = spectr / window_correction

        return frequencies, time, numpy.abs(corrected_spectr)
    
    def find_peak_frequency_time(self, signal=None, min_frequency=100):
        if signal is None:
            return [-1], -1, [-1]
        
        frequencies, times, spectres = signal
        """
        Находит спектр (по времени), в котором максимальное значение амплитуды.
        Возвращает:
        - массив амплитуд (по частотам) для этого времени,
        - соответствующее время,
        - частоту, на которой находится максимум в этом спектре.
        """
        amplitudes = numpy.abs(spectres)  # берём амплитуды
        max_amplitudes_per_time = amplitudes.max(axis=0)  # максимум по частотам для каждого времени
        time_idx = numpy.argmax(max_amplitudes_per_time)     # индекс времени с максимальной амплитудой

        spectrum = amplitudes[:, time_idx]                # спектр (амплитуды) для этого времени
        time = times[time_idx]                            # соответствующее время
        freq_idx = numpy.argmax(spectrum)                 # индекс частоты с наибольшей амплитудой
        frequency = frequencies[freq_idx]                 # сама частота

        return frequency, time, spectrum  