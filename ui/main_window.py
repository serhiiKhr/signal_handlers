import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import numpy as np
import json

from .plot_renderer import PlotRenderer

from analyzers import STFT, Filter
from utils.helpers import get_filename_without_extension
from utils.constants import FREQ_FRAMES
from utils.csv_creator import save_data_to_csv
from utils.execute_json import JSONExecutor

class MainWindow:
    def __init__(self, readers: list, analyzers: list):
        
        self.readers = readers
        self.reader_instance = None
        self.analyzers = [getattr(a, "label", a.__name__) for a in analyzers]
        self.file_path = None
        
        self.root = tk.Tk()
        self.root.title("Аналіз .mera/.dat сигналів")

        self.build_ui()
        
    def open_json_script(self):
        file_path = filedialog.askopenfilename(
            title="Виберіть JSON файл",
            filetypes=[("JSON Files", "*.json")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    execute_settings = json.load(f)
                    
                    executor = JSONExecutor(settings=execute_settings)
                    executor.run()
                    
                print(f"Данные из JSON: {execute_settings}")
            except Exception as e:
                print(f"Ошибка при чтении файла: {e}")
        

    def build_ui(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.grid()
        
        row = 0
        ttk.Button(frm, text="Виконати", command=self.open_json_script).grid(
            column=1, row=row, sticky='e', pady=10
        )
        row += 1
       
        # Кнопки выбора файлов
        for idx, reader in enumerate(self.readers):
            label = getattr(reader, "label", reader.__name__)
            ttk.Button(
                frm,
                text=f"Відкрити {label}",
                command=lambda cls=reader: self.load_file(cls)
            ).grid(column=0, row=idx + row, columnspan=2, sticky='w', pady=5)

        row += len(self.readers)

        # Надпись и список каналов (как раньше — над списком)
        ttk.Label(frm, text="Виберіть канали:").grid(column=0, row=row, columnspan=2, sticky='w', pady=5)
        row += 1
        self.channel_list = tk.Listbox(frm, height=8, selectmode=tk.MULTIPLE, width=50)
        self.channel_list.grid(column=0, row=row, columnspan=2, pady=5)
        row += 1
        
        self.crop_enabled = tk.BooleanVar(value=True)
        chk_crop = ttk.Checkbutton(frm, text="Аналізувати фрагмент", variable=self.crop_enabled)
        chk_crop.grid(column=1, row=row, sticky='w', padx=(0, 10))
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
        self.analyzer_combo = ttk.Combobox(frm, values=self.analyzers)
    
        if self.analyzers:
            self.analyzer_combo.current(0)
            self.analyzer_combo.grid(column=1, row=row, pady=5)      
        row += 1

        ttk.Label(frm, text="Вікно FFT:").grid(column=0, row=row, sticky='e', pady=5)
        self.window = ttk.Combobox(frm, values=["hann", "hamming", "blackman", "boxcar"])
        self.window.set("hann")
        self.window.grid(column=1, row=row, sticky='w')
        row += 1

        ttk.Label(frm, text="Кількість ліній спектру:").grid(column=0, row=row, sticky='e', pady=5)
        powers_of_two = [2**i for i in range(7, 14)]  # 512...8192
        self.nperseg = ttk.Combobox(frm, values=powers_of_two, state="readonly")
        self.nperseg.set(4096)
        self.nperseg.grid(column=1, row=row, sticky='w')
        row += 1

        ttk.Button(frm, text="Аналізувати сигнал", command=self.analyze_selected).grid(
            column=1, row=row, sticky='e', pady=10
        )
        
    def load_file(self, reader):
        self.file_path = reader.load()
        if self.file_path:
            self.reader_instance = reader(filepath=self.file_path)
            channels = self.reader_instance.get_channels()
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
        
        crop_enabled = self.crop_enabled.get()
        start_time = self.start_time_entry.get()
        start_time = float(start_time) if start_time else start_time
        end_time = self.end_time_entry.get()
        end_time = float(end_time) if end_time else end_time
        
        nperseg = int(self.nperseg.get())
        window = self.window.get()
    
        
        analys = self.analyzer_combo.get()
        if analys == getattr(STFT, 'label', __name__):
            self.render_stft_graphs(channels=selected_channels, nperseg=nperseg, window=window, crop_enabled=crop_enabled, start_time=start_time, end_time=end_time)
        else:
            print(f'Analys {analys} is not described')
        
        print(f"Аналізуємо: {selected_channels}, {start_time}-{end_time} c, {window}, {nperseg}")        
     
    def render_stft_graphs(self, channels: list, nperseg: int=0, window: str = 'hann', crop_enabled=False, start_time=None, end_time=None):
        stft = STFT(window=window, nperseg=nperseg)
        file_name = get_filename_without_extension(self.file_path)
        # filter = Filter(lowcut=5, highcut=2000)
        plots = []
        data_row = {
            'filename': file_name
        }
        for channel in channels:
            sampling_rate = self.reader_instance.get_sampling_rate(channel)
            signal = self.reader_instance.read_channel(channel)
            
            if crop_enabled:
                signal = self.reader_instance.slice_signal(signal, sampling_rate, start_time, end_time)
            
            result = stft.analyze(signal=signal, sampling_rate=sampling_rate, min_freq=FREQ_FRAMES['MIN'], max_freq=FREQ_FRAMES['MAX'])
            frequencies, times, amplitudes = result
            frequency, time, max_amplitudes = stft.find_peak_frequency_time(signal=result)

            renderer = PlotRenderer(xdata=frequencies, ydata=max_amplitudes)
            max_idx = np.argmax(max_amplitudes)
            max_x = frequencies[max_idx]
            max_y = max_amplitudes[max_idx]
            minutes = time // 60
            seconds = time % 60
            
            renderer.set_peaks([{'x': max_x, 'y': max_y}])
            
            renderer.set_title(f"{file_name} ({channel})")
            y_units = self.reader_instance.get_y_units(channel=channel)
            renderer.set_ylabel(f'Амплитуда {"(" + y_units + ')' if y_units else ""}')
            renderer.set_xlabel('Частота (Гц)')
            renderer.set_description(f"{max_y:.2f} {y_units if y_units else ''} ({max_x:.2f} Гц).\nНа {int(minutes)} мин {int(seconds):02d} сек")
            renderer.set_xlim((FREQ_FRAMES['MIN'], FREQ_FRAMES['MAX']))
            renderer.set_ylim((0, max_y * 1.3))
            data_row[channel] = f"{max_y:.2f} {y_units if y_units else ''}, {max_x:.2f} Гц"
            
            plots.append(renderer)
            # renderer.show()
            
        save_data_to_csv('D:/MERA/6-я от 11.05.23/Замер3/test-auto-2.csv', [data_row])
        PlotRenderer.show_multiply(plots=plots)


    def run(self):
        self.root.mainloop()
