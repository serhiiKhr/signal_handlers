from readers import BaseReader, MeraReader, DWReader
from analyzers import BaseAnalyzer, STFT

from ui import MainWindow
from utils import LanguageManager

def main():
    lang = LanguageManager()
    print("Программа запущена.")
    
    
    MainWindow(readers=[MeraReader, DWReader], analyzers=[STFT]).run()

if __name__ == "__main__":
    main()