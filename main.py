from readers import BaseReader, MeraReader
from analyzers import BaseAnalyzer, STFT

from ui import MainWindow

def main():
    print("Программа запущена.")
    MainWindow(readers=[MeraReader], analyzers=[STFT]).run()

    # Здесь можно будет создать экземпляры ридеров и процессоров
    # Например:
    # reader = SomeReader()
    # data = reader.read("file.txt")
    #
    # processor = SomeProcessor()
    # result = processor.process(data)
    #
    # print(result)

if __name__ == "__main__":
    main()