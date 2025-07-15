from readers import BaseReader, MeraReader, DWReader
from analyzers import STFT, PSD

from ui import MainWindow
from utils import LanguageManager, Logger

def main():
    lang = LanguageManager()
    Logger.info(lang.get("logger.app_started"))
    
    
    MainWindow(readers=[MeraReader, DWReader], analyzers=[STFT, PSD]).run()

if __name__ == "__main__":
    main()