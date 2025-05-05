WINDOWS = [
    'hann',
    'boxcar',
    'hamming',
    'blackman',
    'bartlett',
    'flattop',
    'kaiser'
]
ANALYSIS = {'STFT': 'stft'}
FREQ_FRAMES = {'MIN': 5, 'MAX': 2000}
DEFAULT_IMG_EXTENSION = '.png'

NPERSEGS = [2**i for i in range(7, 14)]

DEFAULT_WINDOW = WINDOWS[0]
DEFAULT_NPERSEG = 4096
DEFAULT_MIN_FREQ = 5
DEFAULT_MAX_FREQ = 2000
DEFAULT_OVERLAAP_PERCENT = 50
DEFAULT_MIN_DISPLAY_FREQ = 100

class SourceProgramm:
    def __init__(self, id: str, name: str, extensions: list):
        self.id = id
        self.name = name
        self.extensions = extensions
        
MERA = SourceProgramm(id='mera', name='MERA', extensions=['.mera'])
SOURCE_PROGRAMS = [MERA]


def get_windows():
    return WINDOWS