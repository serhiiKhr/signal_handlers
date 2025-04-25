WINDOWS = {'HANNING': 'hanning', 'BLACKMANHARRIS': 'blackmanharris'}
ANALYSIS = {'STFT': 'stft'}
FREQ_FRAMES = {'MIN': 5, 'MAX': 2000}


def get_windows():
    return WINDOWS

def compare_window(win_1: str, win_2: str):
    return WINDOWS[win_1] == win_2