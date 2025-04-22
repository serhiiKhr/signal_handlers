from readers import BaseReader
from analyzers import BaseAnalyzer

from ui import MainWindow

def main():
    print("Программа запущена.")
    MainWindow(readers=[], analyzers=[]).run()

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