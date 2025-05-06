import numpy
from scipy.signal.windows import hann, blackmanharris, boxcar, hamming, bartlett, flattop, kaiser
from scipy.signal import stft

from utils import ANALYSIS, LanguageManager
from utils.constants import (
    DEFAULT_WINDOW,
    DEFAULT_NPERSEG,
    DEFAULT_MIN_FREQ,
    DEFAULT_MAX_FREQ,
    DEFAULT_OVERLAAP_PERCENT,
    DEFAULT_MIN_DISPLAY_FREQ
)

from .base import BaseAnalyzer

class STFT(BaseAnalyzer):
    id: str = ANALYSIS['STFT']
    label: str = LanguageManager().get('stft.label')
    def __init__(self,
                 nperseg: int = DEFAULT_WINDOW,
                 window: str = DEFAULT_NPERSEG,
                 min_freq: float = DEFAULT_MIN_FREQ, 
                 max_freq: float = DEFAULT_MAX_FREQ, 
                 overlap_percent: float = DEFAULT_OVERLAAP_PERCENT,
                 min_display_freq: float = DEFAULT_MIN_DISPLAY_FREQ
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
    
    def frame_signal(self, signal, min_freq=None, max_freq=None):
        if min_freq is None and max_freq is None:
            return signal
        
        frequencies, time, spectr = signal
                
        freq_mask = (frequencies >= min_freq) & (frequencies <= max_freq)
        filtered_frequencies = frequencies[freq_mask]
        filtered_spectr = numpy.abs(spectr[freq_mask, :])
        
        return filtered_frequencies, time, filtered_spectr
    
    
    def analyze(self, signal, **kwargs):
        sampling_rate = kwargs.get('sampling_rate')
        min_freq = kwargs.get('min_freq')
        max_freq = kwargs.get('max_freq')
        
        _nperseg = self.nperseg
        if len(signal) < self.nperseg:
            _nperseg = len(signal)
        
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
                        
        noverlap = 0
        if self.overlap_percent is not None and isinstance(self.overlap_percent, (float, int)) and self.overlap_percent > 0:
            noverlap = int((self.overlap_percent / 100) * _nperseg)

        frequencies, time, spectr = stft(
            signal,
            fs=sampling_rate,
            window=window,
            nperseg=_nperseg,
            noverlap=noverlap,
            boundary='zeros'
        )
        window_correction = numpy.sum(window) / _nperseg
        corrected_spectr = spectr / window_correction
        corrected_spectr[0, :] = 0

        return self.frame_signal((frequencies, time, numpy.abs(corrected_spectr)), min_freq=min_freq, max_freq=max_freq) 
    
    def find_peak_frequency_time(self, signal=None, min_frequency=None):
        if signal is None:
            return [-1], -1, [-1]

        frequencies, times, spectres = signal
        """
        Finds the spectrum (over time) where the maximum amplitude occurs.
        Returns:
        - an array of amplitudes (over frequencies) at that time,
        - the corresponding time,
        - the frequency at which the maximum in that spectrum is located.
        """
        max_frequency = numpy.max(frequencies)
        amplitudes = numpy.abs(spectres) # extract amplitudes

        max_amplitudes_per_time = amplitudes.max(axis=0) # maximum over frequencies for each time
        
        # If min_frequency is not set, proceed as before
        if min_frequency is None or min_frequency > max_frequency:
            time_idx = numpy.argmax(max_amplitudes_per_time) # Index of the time with the maximum amplitude
        else:
            # Sort max_amplitudes_per_time in descending order while preserving indices
            sorted_indices = numpy.argsort(max_amplitudes_per_time)[::-1]  # Indices from maximum to minimum
            sorted_max_amplitudes = max_amplitudes_per_time[sorted_indices]

            result_index = 0  # Index to be returned
            for i in range(len(sorted_max_amplitudes)):
                max_amplitude_index = sorted_indices[i]  # The actual time index
                max_freq = frequencies[numpy.argmax(amplitudes[:, max_amplitude_index])] # frequency for this amplitude
                
                if max_freq >= min_frequency:
                    result_index = max_amplitude_index # found the index that matches
                    break
            
            # If no matching index is found, return None
            if result_index == 0 and frequencies[numpy.argmax(amplitudes[:, sorted_indices[0]])] < min_frequency:
                return self.find_peak_frequency_time(signal=signal, min_frequency=None)
            
            time_idx = result_index

        spectrum = amplitudes[:, time_idx]  # spectrum (amplitudes) for this time
        time = times[time_idx]              # corresponding time
        freq_idx = numpy.argmax(spectrum)   # frequency index with the highest amplitude
        frequency = frequencies[freq_idx]   # the frequency itself

        return frequency, time, spectrum