WINDOWS = [
    'hann',
    'boxcar',
    'hamming',
    'blackman',
    'bartlett',
    'flattop',
    'kaiser'
]
ANALYSIS = {'STFT': 'stft', 'PSD': 'psd'}
FREQ_FRAMES = {'MIN': 5, 'MAX': 2000}
DEFAULT_IMG_EXTENSION = '.png'

UNITS = {
    "ACCEL_MS2": "m/s²",
    "ACCEL_G": "g",
    "PSD_MS2": "m²/s⁴/Hz",
    "PSD_G": "g²/Hz",
    "FREQ": "Hz",
    "TIME": "s",
    "VARIANCE_MS2": "m²/s⁴",
    "VARIANCE_G": "g²"
}

G = 9.80665

NPERSEGS = [2**i for i in range(7, 14)]

DEFAULT_WINDOW = WINDOWS[0]
DEFAULT_NPERSEG = 4096
DEFAULT_MIN_FREQ = 5
DEFAULT_MAX_FREQ = 2000
DEFAULT_OVERLAAP_PERCENT = 50
DEFAULT_MIN_DISPLAY_FREQ = 100

PSD_SCALINGS = ['density', 'spectrum']
DEFAULT_PSD_SCALING = 'density'

class SourceProgramm:
    def __init__(self, id: str, name: str, extensions: list):
        self.id = id
        self.name = name
        self.extensions = extensions
        
MERA = SourceProgramm(id='mera', name='MERA', extensions=['.mera'])
DEWESOFT = SourceProgramm(id='dewesoft', name='Dewesoft', extensions=['.dxd']) 
SOURCE_PROGRAMS = [MERA, DEWESOFT]

def get_windows():
    return WINDOWS