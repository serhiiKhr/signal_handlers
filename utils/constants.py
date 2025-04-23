WINDOWS = {'HANNING': 'hanning', 'BLACKMANHARRIS': 'blackmanharris'}

def get_windows():
    return WINDOWS

def compare_window(win_1: str, win_2: str):
    return WINDOWS[win_1] == win_2