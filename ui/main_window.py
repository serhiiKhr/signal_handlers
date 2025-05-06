import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk, filedialog
import numpy as np
import json

from .plot_renderer import PlotRenderer

from analyzers import STFT, Filter
from utils.helpers import get_filename_without_extension
from utils.constants import FREQ_FRAMES
from utils.csv_creator import save_data_to_csv
from utils.execute_json import JSONExecutor

from .modals import STFTSettings

class MainWindow:
    def __init__(self, readers: list, analyzers: list):
        
        self.readers = readers
        self.reader_instance = None
        self.analyzers = [getattr(a, "label", a.__name__) for a in analyzers]
        self.file_path = None
        
        
        
        self.root = tk.Tk()
        self.root.title("Аналіз сигналів (MERA, DWSoft)")
        
        self.method_settings = None

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
        
        self.crop_enabled = tk.BooleanVar(value=False)
        chk_crop = ttk.Checkbutton(frm, text="Аналізувати фрагмент", variable=self.crop_enabled, command=self.toggle_crop_widgets)
        chk_crop.grid(column=1, row=row, sticky='w', padx=(0, 10))
        row += 1

        ttk.Label(frm, text="Початок аналізу [с]:").grid(column=0, row=row, sticky='e', pady=5)
        self.start_time_entry = ttk.Entry(frm, state="disabled")
        self.start_time_entry.insert(0, "0.0")
        self.start_time_entry.grid(column=1, row=row, sticky='w')
        row += 1

        ttk.Label(frm, text="Кінець аналізу [с]:").grid(column=0, row=row, sticky='e', pady=5)
        self.end_time_entry = ttk.Entry(frm, state="disabled")
        self.end_time_entry.insert(0, "1.0")
        self.end_time_entry.grid(column=1, row=row, sticky='w')
        row += 1
        
        ttk.Label(frm, text="Метод аналізу:").grid(column=0, row=row, sticky='e', pady=5)
        self.analyzer_combo = ttk.Combobox(frm, values=self.analyzers)
    
        if self.analyzers:
            self.analyzer_combo.current(0)
            self.analyzer_combo.grid(column=1, row=row, pady=5)      
        row += 1
        self.get_default_settings(analys=self.analyzer_combo.get())
        

        ttk.Button(frm, text="Налаштування", command=self.open_settings_dialog).grid(
            column=1, row=row, sticky='e', pady=10
        )
        row += 1
        
         # Чекбокс для сохранения статистики
        self.save_stats = tk.BooleanVar(value=False)
        save_stats_chk = ttk.Checkbutton(
            frm,
            text="Зберігати статистику у файл",
            variable=self.save_stats,
            command=self.toggle_stats_widgets  # вызов обработчика
        )
        save_stats_chk.grid(column=1, row=row, sticky='w', padx=(0, 10))
        row += 1

        # Метка и поле ввода пути
        ttk.Label(frm, text="Шлях до файлу:").grid(column=0, row=row, sticky='e', pady=5)
        self.stats_path = tk.StringVar()
        self.stats_entry = ttk.Entry(frm, textvariable=self.stats_path, state='disabled')  # начально — норм, если save_stats=True
        self.stats_entry.grid(column=1, row=row, sticky='w')
        row += 1

        # Кнопка выбора файла
        self.stats_button = ttk.Button(frm, text="Оберіть шлях збереження...", state='disabled', command=self.choose_stats_path)
        self.stats_button.grid(column=1, row=row, sticky='e', pady=10)
        row += 1

        ttk.Button(frm, text="Аналізувати сигнал", command=self.analyze_selected).grid(
            column=1, row=row, sticky='e', pady=10
        )
        
    def toggle_crop_widgets(self):
        state = 'normal' if self.crop_enabled.get() else 'disabled'
        self.start_time_entry.configure(state=state)
        self.end_time_entry.configure(state=state)
        
    def toggle_stats_widgets(self):
        """Включить/отключить поля в зависимости от состояния чекбокса."""
        state = 'normal' if self.save_stats.get() else 'disabled'
        self.stats_entry.configure(state=state)
        self.stats_button.configure(state=state)

    def choose_stats_path(self):
        """Открыть диалог выбора пути для сохранения файла."""
        filepath = filedialog.askdirectory(title="Оберіть папку для збереження")
        if filepath:
            self.stats_path.set(filepath)

        
    def open_settings_dialog(self):
        analys = self.analyzer_combo.get()
        if analys == getattr(STFT, 'label', __name__):
            
            dialog = STFTSettings(data=self.method_settings)
            dialog.open(self.root)
            settings = dialog.get_settings()
            if settings:
                self.method_settings = {
                    **settings,
                    'name': 'stft'
                }
        else:
            raise ValueError(f"Невідомий метод: {analys}")
    
    def get_default_settings(self, analys):
        if analys == getattr(STFT, 'label', __name__):
            dialog = STFTSettings()
            settings = dialog.get_settings()
            self.method_settings = {
                **settings,
                'name': 'stft'
            }
            print('self.method_settings ==>', self.method_settings)
        else:
            raise ValueError(f"Невідомий метод: {analys}")
            
        
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
        
        min_freq = (self.method_settings or {}).get('min_freq', FREQ_FRAMES['MIN'])
        max_freq = (self.method_settings or {}).get('min_freq', FREQ_FRAMES['MAX'])
        
       
        
        analys = self.analyzer_combo.get()
        if analys == getattr(STFT, 'label', __name__):
            self.render_stft_graphs(
                channels=selected_channels, 
                crop_enabled=crop_enabled, 
                start_time=start_time, 
                end_time=end_time, 
                method_settings=self.method_settings
            )
        else:
            print(f'Analys {analys} is not described')
        
     
    def render_stft_graphs(
        self, 
        channels: list, 
        crop_enabled=False, 
        start_time=None, 
        end_time=None,
        method_settings=None
    ):
        if method_settings is None:
            print(f'Something went wrong. Could not find method_settings ({self.method_settings})')
            
        window = (self.method_settings or {}).get('window')
        nperseg = (self.method_settings or {}).get('nperseg')
        
        min_freq = (self.method_settings or {}).get('min_freq')
        max_freq = (self.method_settings or {}).get('max_freq')
        overlap_percent = (self.method_settings or {}).get('overlap_percent')
        min_display_freq = (self.method_settings or {}).get('min_display_freq')
    
        stft = STFT(window=window, nperseg=nperseg, min_freq=min_freq, max_freq=max_freq, overlap_percent=overlap_percent, min_display_freq=min_display_freq)
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
            
            result = stft.analyze(signal=signal, sampling_rate=sampling_rate, min_freq=min_freq, max_freq=max_freq)
            frequencies, times, amplitudes = result
            frequency, time, max_amplitudes = stft.find_peak_frequency_time(signal=result, min_frequency=min_display_freq)

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
            
        stats_path = self.stats_path.get()
        if self.save_stats.get() and stats_path:
            stats_file_name = datetime.now().strftime("%Y-%m-%d__%H-%M-%S")
            save_data_to_csv(f'{stats_path}/{stats_file_name}.csv', [data_row])
            
        # 
        PlotRenderer.show_multiply(plots=plots)


    def run(self):
        self.root.mainloop()
