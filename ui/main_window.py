import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

class MainWindow:
    def __init__(self, readers: list, analyzers: list):
        self.readers = readers
        self.analyzers = analyzers
        self.selected_analyzer_class = None
        
        self.root = tk.Tk()
        self.root.title("Аналіз .mera/.dat сигналів")

        self.file_buttons = [
            {"text": "Відкрити .mera файл", "command": self.load_mera_file},
            # Можно добавить больше кнопок в будущем
        ]

        self.build_ui()

    def build_ui(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.grid()

        # Кнопки выбора файлов
        for idx, reader in enumerate(self.readers):
            label = getattr(reader, "label", reader.__name__)
            ttk.Button(
                self.frm,
                text=f"Відкрити {label}",
                command=lambda cls=reader: self.load_file(cls)
            ).grid(column=0, row=idx, columnspan=2, sticky='w', pady=5)

        row = len(self.file_buttons)

        # Надпись и список каналов (как раньше — над списком)
        ttk.Label(frm, text="Виберіть канали:").grid(column=0, row=row, columnspan=2, sticky='w', pady=5)
        row += 1
        self.channel_list = tk.Listbox(frm, height=8, selectmode=tk.MULTIPLE, width=50)
        self.channel_list.grid(column=0, row=row, columnspan=2, pady=5)
        row += 1

        ttk.Label(frm, text="Початок аналізу [с]:").grid(column=0, row=row, sticky='e', pady=5)
        self.start_time_entry = ttk.Entry(frm)
        self.start_time_entry.insert(0, "0.0")
        self.start_time_entry.grid(column=1, row=row, sticky='w')
        row += 1

        ttk.Label(frm, text="Кінець аналізу [с]:").grid(column=0, row=row, sticky='e', pady=5)
        self.end_time_entry = ttk.Entry(frm)
        self.end_time_entry.insert(0, "1.0")
        self.end_time_entry.grid(column=1, row=row, sticky='w')
        row += 1
        
        ttk.Label(frm, text="Метод аналізу:").grid(column=0, row=row, sticky='e', pady=5)
        self.analyzer_combo = ttk.Combobox(
            frm,
            values=[getattr(a, "label", a.__name__) for a in self.analyzers]
        )
        if len(self.analyzers) > 0:
            self.analyzer_combo.current(0)
            self.analyzer_combo.grid(column=1, row=row, pady=5)
            self.analyzer_combo.bind("<<ComboboxSelected>>", self.on_analyzer_selected)
            self.selected_analyzer_class = self.analyzers[0]
            
        row += 1

        ttk.Label(frm, text="Вікно FFT:").grid(column=0, row=row, sticky='e', pady=5)
        self.window_combo = ttk.Combobox(frm, values=["hann", "hamming", "blackman", "boxcar"])
        self.window_combo.set("hann")
        self.window_combo.grid(column=1, row=row, sticky='w')
        row += 1

        ttk.Label(frm, text="Кількість ліній спектру:").grid(column=0, row=row, sticky='e', pady=5)
        self.fft_lines_entry = ttk.Entry(frm)
        self.fft_lines_entry.insert(0, "4096")
        self.fft_lines_entry.grid(column=1, row=row, sticky='w')
        row += 1

        ttk.Label(frm, text="Одиниці сигналу:").grid(column=0, row=row, sticky='e', pady=5)
        self.unit_combo = ttk.Combobox(frm, values=["Без змін", "g → m/s²", "m/s² → g"])
        self.unit_combo.set("Без змін")
        self.unit_combo.grid(column=1, row=row, sticky='w')
        row += 1

        ttk.Label(frm, text="Тип перетворення:").grid(column=0, row=row, sticky='e', pady=5)
        self.transform_combo = ttk.Combobox(frm, values=["Прискорення", "Швидкість", "Переміщення"])
        self.transform_combo.set("Прискорення")
        self.transform_combo.grid(column=1, row=row, sticky='w')
        row += 1

        ttk.Button(frm, text="Аналізувати сигнал", command=self.analyze_selected).grid(
            column=1, row=row, sticky='e', pady=10
        )
        
        
    def on_analyzer_selected(self, event):
        selected_index = self.analyzer_combo.current()
        self.selected_analyzer_class = self.analyzer_classes[selected_index]
        print(f"Вибрано метод: {self.selected_analyzer_class.__name__}")
        
    def load_file(self, reader):
        print(f"Викликаємо: {reader.__name__}")


    def load_mera_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("MERA files", "*.mera"), ("DAT files", "*.dat")])
        if file_path:
            print(f"Файл відкрито: {file_path}")
            # TODO: обработка файла и обновление self.channel_list

    def analyze_selected(self):
        selected_channels = [self.channel_list.get(i) for i in self.channel_list.curselection()]
        start_time = self.start_time_entry.get()
        end_time = self.end_time_entry.get()
        window = self.window_combo.get()
        fft_lines = self.fft_lines_entry.get()
        units = self.unit_combo.get()
        transform = self.transform_combo.get()

        print(f"Аналізуємо: {selected_channels}, {start_time}-{end_time} c, {window}, {fft_lines}, {units}, {transform}")
        # TODO: выполнить анализ

    def run(self):
        self.root.mainloop()
