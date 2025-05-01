WINDOWS = {'HANNING': 'hanning', 'BLACKMANHARRIS': 'blackmanharris'}
ANALYSIS = {'STFT': 'stft'}
FREQ_FRAMES = {'MIN': 5, 'MAX': 2000}
DEFAULT_IMG_EXTENSION = '.png'


class SourceProgramm:
    def __init__(self, id: str, name: str, extensions: list):
        self.id = id
        self.name = name
        self.extensions = extensions
        
MERA = SourceProgramm(id='mera', name='MERA', extensions=['.mera'])
SOURCE_PROGRAMS = [MERA]


def get_windows():
    return WINDOWS

def compare_window(win_1: str, win_2: str):
    return WINDOWS[win_1] == win_2