import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import filedialog
import numpy as np
import os

class MainWindow:
    def __init__(self, readers: list, analyzers: list):
        
        self.readers = readers
        self.reader_instance = None
        self.analyzers = analyzers
        self.analyzer_instance = None
        
        self.file_path = None
        
        self.root = tk.Tk()
        self.root.title("Аналіз .mera/.dat сигналів")

        self.build_ui()

    def build_ui(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.grid()

        # Кнопки выбора файлов
        for idx, reader in enumerate(self.readers):
            label = getattr(reader, "label", reader.__name__)
            ttk.Button(
                frm,
                text=f"Відкрити {label}",
                command=lambda cls=reader: self.load_file(cls)
            ).grid(column=0, row=idx, columnspan=2, sticky='w', pady=5)

        row = len(self.readers)

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
            self.analyzer_instance = self.analyzers[0]
            
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
        self.analyzer_instance = self.analyzer_classes[selected_index]
        print(f"Вибрано метод: {self.analyzer_instance.__name__}")
        
    def load_file(self, reader):
        self.reader_instance = reader()
        file_path = self.reader_instance.load()
        self.file_path = file_path
        channels = self.reader_instance.get_channels(file_path)
        self.update_channels(channels)
              
      
    def update_channels(self, channels: list):
        if not channels:
            messagebox.showerror('data is not selected')
            return
        
        self.channel_list.delete(0, tk.END)
    
        for channel in channels:
            self.channel_list.insert(tk.END, channel)

    def analyze_selected(self):
        selected_channels = [self.channel_list.get(i) for i in self.channel_list.curselection()]
        if not selected_channels:
            messagebox.showwarning("Увага", "Виберіть хоча б один канал.")
            return
        
        start_time = self.start_time_entry.get()
        end_time = self.end_time_entry.get()
        fft_lines = self.fft_lines_entry.get()
         
        window = self.window_combo.get()
        
        units = self.unit_combo.get()
        transform = self.transform_combo.get()
        
        for selected_channel in selected_channels:
            self.analyze_channel(ch_name=selected_channel)

        print(f"Аналізуємо: {selected_channels}, {start_time}-{end_time} c, {window}, {fft_lines}, {units}, {transform}")        
        
    def analyze_channel(self, ch_name: str):
        signal = self.reader_instance.read_channel(self.file_path, ch_name)
        # if polyTX == 0:
        #     signal = k1 * (signal - k0)
        # else:
        #     signal = k1 * signal + k0

        # if convert_unit == "g → m/s²":
        #     signal *= 9.80665
        # elif convert_unit == "m/s² → g":
        #     signal /= 9.80665

        # if transform_type == "Швидкість":
        #     signal = cumtrapz(signal, dx=1/freq)
        # elif transform_type == "Переміщення":
        #     signal = cumtrapz(cumtrapz(signal, dx=1/freq), dx=1/freq)

        # time = np.linspace(t_start, t_end, len(signal), endpoint=False)
        # window = get_window(win_type, len(signal))
        # signal_win = (signal - np.mean(signal)) * window
        # spectrum = 2 * np.abs(fft(signal_win, n=n_fft))[:n_fft//2] / len(signal_win)
        # freqs = fftfreq(n_fft, d=1/freq)[:n_fft//2]

        # fig, axs = plt.subplots(2, 1, figsize=(12, 8))
        # axs[0].plot(time, signal)
        # axs[0].set_title(f"Сигнал: {name} ({t_start:.3f}–{t_end:.3f} с)")
        # axs[0].set_xlabel("Час [с]")
        # axs[0].set_ylabel("Амплітуда")
        # axs[0].grid(True)

        # axs[1].plot(freqs, spectrum)
        # axs[1].set_title(f"АЧХ (FFT, {win_type}, {n_fft} ліній)")
        # axs[1].set_xlabel("Частота [Гц]")
        # axs[1].set_ylabel("Амплітуда")
        # axs[1].grid(True)

        # plt.tight_layout()
        # plt.show()


    def run(self):
        self.root.mainloop()
