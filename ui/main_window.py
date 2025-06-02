import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk, filedialog
import numpy as np
import json
import traceback

from .plot_renderer import PlotRenderer

from analyzers import STFT, Filter
from utils.helpers import get_filename_without_extension, get_file_path
from utils.constants import FREQ_FRAMES, SOURCE_PROGRAMS
from utils.csv_creator import save_data_to_csv
from utils.language_manager import LanguageManager
from utils.logger import Logger


from engine import SignalEngine 

from .modals import STFTSettings, TimeframeSettings

class MainWindow:
    def __init__(self, readers: list, analyzers: list):
        
        self.readers = readers
        self.reader_instance = None
        self.analyzers = [getattr(a, "label", a.__name__) for a in analyzers]
        self.file_path = None
        
        self.source_program = None
        
        self.lang = LanguageManager()
        
        
        programs = [pr.name for pr in SOURCE_PROGRAMS]
        self.root = tk.Tk()
        self.root.title(self.lang.get("title", programs=", ".join(programs)))
        
        self.method_settings = None

        self.build_ui()
        
    def open_json_script(self):
        file_path = filedialog.askopenfilename(
            title=self.lang.get("ui.select_json"),
            filetypes=[(self.lang.get("ui.select_json_window"), "*.json")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    execute_settings = json.load(f)
                    
                    executor = SignalEngine(settings=execute_settings)
                    
                    # executor = JSONExecutor(settings=execute_settings)
                    executor.start()
                
            except Exception as e:
                traceback.format_exc()
                Logger.error(self.lang.get("logger.file_read_error", error=e))        

    def build_ui(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.grid()
        
        row = 0
        ttk.Button(frm, text=self.lang.get("ui.execute"), command=self.open_json_script).grid(
            column=1, row=row, sticky='e', pady=10
        )
        row += 1
       
        # File selection buttons
        for idx, reader in enumerate(self.readers):
            label = getattr(reader, "label", reader.__name__)
            ttk.Button(
                frm,
                text=self.lang.get("ui.open_the_file", file=label),
                command=lambda cls=reader: self.load_file(cls)
            ).grid(column=0, row=idx + row, columnspan=2, sticky='w', pady=5)

        row += len(self.readers)

        # Label and channel list
        ttk.Label(frm, text=self.lang.get("ui.select_channels")).grid(column=0, row=row, columnspan=2, sticky='w', pady=5)
        row += 1
        self.channel_list = tk.Listbox(frm, height=8, selectmode=tk.MULTIPLE, width=50)
        self.channel_list.grid(column=0, row=row, columnspan=2, pady=5)
        row += 1
        
        ttk.Button(frm, text=self.lang.get("ui.settings"), command=self.open_timeframe_dialog).grid(
            column=1, row=row, sticky='e', pady=10
        )
        row += 1
        ttk.Label(frm, text=self.lang.get("ui.start_of_analysis")).grid(column=0, row=row, sticky='w', pady=5)
        scroll_container = ttk.Frame(frm)
        scroll_container.grid(column=0, row=row, columnspan=2, sticky="w", pady=5)

        canvas = tk.Canvas(scroll_container, height=100, width=300, highlightthickness=0)  # Ограничим и по высоте, и по ширине
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)

        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=False)
        scrollbar.pack(side="right", fill="y")

        # Пример наполнения
        for i in range(20):
            row_frame = ttk.Frame(scrollable_frame, width=300)
            row_frame.pack(fill="x", padx=5, pady=2)

            ttk.Label(row_frame, text=f"Элемент {i}A", width=11).grid(row=0, column=0, sticky="w", padx=(0, 5))
            ttk.Label(row_frame, text=f"Элемент {i}B", width=6).grid(row=0, column=1, sticky="w", padx=(0, 5))
            ttk.Label(row_frame, text=f"Элемент {i}C", width=6).grid(row=0, column=2, sticky="w", padx=(0, 5))
            ttk.Label(row_frame, text=f" ", width=2).grid(row=0, column=3, sticky="w", padx=(0, 5))

            # row_frame.columnconfigure(5, weight=1)  # Растянуть колонку для "прыжка" к правому краю
            # row_frame.columnconfigure(6, weight=0)
            ttk.Button(row_frame, text="Изменить", width=7).grid(row=0, column=4, sticky="e", padx=(0, 5))
            ttk.Button(row_frame, text="Удалить", width=7).grid(row=0, column=5, sticky="e")
            
            row += 1
            
        for child in scrollable_frame.winfo_children():
            try:
                for ch in child.winfo_children():
                    ch.configure(state='disabled')
            except tk.TclError:
                pass  # Некоторые виджеты (например, Label) не поддерживают 'state'
   
        self.crop_enabled = tk.BooleanVar(value=False)
        chk_crop = ttk.Checkbutton(frm, text=self.lang.get("ui.analyze_fragment"), variable=self.crop_enabled, command=self.toggle_crop_widgets)
        chk_crop.grid(column=1, row=row, sticky='w', padx=(0, 10))
        row += 1

        ttk.Label(frm, text=self.lang.get("ui.start_of_analysis")).grid(column=0, row=row, sticky='e', pady=5)
        self.start_time_entry = ttk.Entry(frm, state="disabled")
        self.start_time_entry.insert(0, "0.0")
        self.start_time_entry.grid(column=1, row=row, sticky='w')
        row += 1

        ttk.Label(frm, text=self.lang.get("ui.end_of_analysis")).grid(column=0, row=row, sticky='e', pady=5)
        self.end_time_entry = ttk.Entry(frm, state="disabled")
        self.end_time_entry.insert(0, "1.0")
        self.end_time_entry.grid(column=1, row=row, sticky='w')
        row += 1
        
        ttk.Label(frm, text=self.lang.get("ui.analysis_method")).grid(column=0, row=row, sticky='e', pady=5)
        self.analyzer_combo = ttk.Combobox(frm, values=self.analyzers)
    
        if self.analyzers:
            self.analyzer_combo.current(0)
            self.analyzer_combo.grid(column=1, row=row, pady=5)      
        row += 1
        self.get_default_settings(analys=self.analyzer_combo.get())
        

        ttk.Button(frm, text=self.lang.get("ui.settings"), command=self.open_settings_dialog).grid(
            column=1, row=row, sticky='e', pady=10
        )
        row += 1
        
        # Checkbox for saving statistics
        self.save_stats = tk.BooleanVar(value=False)
        save_stats_chk = ttk.Checkbutton(
            frm,
            text=self.lang.get("ui.save_statistics_to_file"),
            variable=self.save_stats,
            command=self.toggle_stats_widgets  # Handler call
        )
        save_stats_chk.grid(column=1, row=row, sticky='w', padx=(0, 10))
        row += 1

        # Label and path entry field
        ttk.Label(frm, text=self.lang.get("ui.file_path")).grid(column=0, row=row, sticky='e', pady=5)
        self.stats_path = tk.StringVar()
        self.stats_entry = ttk.Entry(frm, textvariable=self.stats_path, state='disabled')  # Disabled if save_stats is False
        self.stats_entry.grid(column=1, row=row, sticky='w')
        row += 1

        # File selection button
        self.stats_button = ttk.Button(frm, text=self.lang.get("ui.choose_save_path"), state='disabled', command=self.choose_stats_path)
        self.stats_button.grid(column=1, row=row, sticky='e', pady=10)
        row += 1
        
         # Checkbox for showing graphs
        self.show_graph = tk.BooleanVar(value=False)
        show_graph_chk = ttk.Checkbutton(
            frm,
            text=self.lang.get("ui.show_result_graphs"),
            variable=self.show_graph
        )
        show_graph_chk.grid(column=1, row=row, sticky='w', padx=(0, 10))
        row += 1

        ttk.Button(frm, text=self.lang.get("ui.analyze_signal"), command=self.analyze_selected).grid(
            column=1, row=row, sticky='e', pady=10
        )
        
    def open_timeframe_dialog(self, timeframe=None):
        analys = self.analyzer_combo.get()
        dialog = TimeframeSettings(data=timeframe)
        dialog.open(self.root)
        settings = dialog.get_settings()
        print('settings=>', settings)
        
    def toggle_crop_widgets(self):
        state = 'normal' if self.crop_enabled.get() else 'disabled'
        self.start_time_entry.configure(state=state)
        self.end_time_entry.configure(state=state)
        
    def toggle_stats_widgets(self):
        """Enable or disable fields depending on the checkbox state."""
        state = 'normal' if self.save_stats.get() else 'disabled'
        # self.stats_entry.configure(state=state)
        self.stats_button.configure(state=state)

    def choose_stats_path(self):
        """Open a dialog to select a path for saving the file."""
        filepath = filedialog.askdirectory(title=self.lang.get("ui.choose_folder_to_save"))
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
            Logger.warning(self.lang.get("logger.unknown_method", method=analys))
            return
    
    def get_default_settings(self, analys):
        if analys == getattr(STFT, 'label', __name__):
            dialog = STFTSettings()
            settings = dialog.get_settings()
            self.method_settings = {
                **settings,
                'name': 'stft'
            }
            Logger.debug(f'self.method_settings: {self.method_settings}')
        else:
            Logger.warning(self.lang.get("logger.unknown_method", method=analys))
            return            
        
    def load_file(self, reader):
        self.file_path = reader.load()
        if self.file_path:
            self.reader_instance = reader(filepath=self.file_path)
            channels = self.reader_instance.get_channels()
            self.source_program = reader.id
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
            messagebox.showwarning(self.lang.get("ui.warning"), self.lang.get("ui.select_at_least_one_channel"))
            return
        
        crop_enabled = self.crop_enabled.get()
        start_time = self.start_time_entry.get()
        end_time = self.end_time_entry.get()
        
        if crop_enabled:
            if not start_time or not end_time:
                messagebox.showwarning(self.lang.get("ui.warning"), self.lang.get("ui.crop_time_missing"))
                return

            try:
                start_time = float(start_time)
                end_time = float(end_time)
            except ValueError:
                messagebox.showwarning(self.lang.get("ui.warning"), self.lang.get("ui.crop_time_invalid"))
                return

            if end_time <= start_time:
                messagebox.showwarning(self.lang.get("ui.warning"), self.lang.get("ui.crop_time_order_error"))
                return
          
        settings = SignalEngine.generate_settings_obj(
            file_path=self.file_path,
            source_program=self.source_program,
            selected_channels=selected_channels,
            method_settings=self.method_settings,
            crop_enabled=crop_enabled,
            start_time=start_time,
            end_time=end_time,
            save_stats=self.save_stats.get(),
            stats_path=self.stats_path.get(),
            show_graph=self.show_graph.get()
        )        

        executor = SignalEngine(settings=settings)
        
        executor.start()

    def run(self):
        self.root.mainloop()
