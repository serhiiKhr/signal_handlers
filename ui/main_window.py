import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk, filedialog
import numpy as np
import json
import traceback
from typing import TypedDict, List
import uuid

from .plot_renderer import PlotRenderer

from analyzers import STFT, PSD, Filter
from utils.helpers import get_filename_without_extension, get_file_path, find_index
from utils.constants import FREQ_FRAMES, SOURCE_PROGRAMS
from utils.csv_creator import save_data_to_csv
from utils.language_manager import LanguageManager
from utils.logger import Logger


from engine import SignalEngine 

from .modals import STFTSettings, PSDSettings, TimeframeSettings


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None

        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip or not self.text:
            return

        x = y = 0
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 20

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)  # window frame removing
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip,
            text=self.text,
            justify='left',
            background="#ffffe0",
            relief='solid',
            borderwidth=1,
            font=("tahoma", "8", "normal")
        )
        label.pack(ipadx=4)

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
            
            
class Timeframe(TypedDict):
    id: str
    name: str
    start: float
    end: float

class MainWindow:
    def __init__(self, readers: list, analyzers: list):
        
        self.readers = readers
        self.reader_instance = None
        self.analyzers = analyzers
        self.file_path = None
        
        self.source_program = None
        
        self.lang = LanguageManager()
        
        
        programs = [pr.name for pr in SOURCE_PROGRAMS]
        self.root = tk.Tk()
        self.root.title(self.lang.get("title", programs=", ".join(programs)))
        
        self.method_settings = None
        
        self.timeframes: List[Timeframe] = []

        # self.timeframes.append({"id": '1', "name": "test 1", "start": 0.01, "end": 1.00})
        # self.timeframes.append({"id": '2', "name": "test 2", "start": 1.01, "end": 33.00})
        # self.timeframes.append({"id": '3', "name": "test 3", "start": 1.01, "end": 33.00})
        # self.timeframes.append({"id": '4', "name": "test 4", "start": 1.01, "end": 33.00})
        # self.timeframes.append({"id": '5', "name": "test 5", "start": 1.01, "end": 33.00})
        # self.timeframes.append({"id": '6', "name": "test 6", "start": 1.01, "end": 33.00})
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

    def render_timeframes(self, timeframes_frame, timeframes):
        for child in timeframes_frame.winfo_children():
            child.destroy()
        
        for timeframe in timeframes:
            row_frame = ttk.Frame(timeframes_frame, width=300)
            row_frame.pack(fill="x", padx=5, pady=2)

            name = ttk.Label(row_frame, text=f"{timeframe['name']}", width=7)
            name.grid(row=0, column=0, sticky="w", padx=(0, 2))
            
            ToolTip(name, timeframe['name'])
            
            ttk.Label(row_frame, text=f"{self.lang.get('timeframe.start')}: {timeframe['start']}", width=13).grid(row=0, column=1, sticky="w", padx=(0, 2))
            ttk.Label(row_frame, text=f"{self.lang.get('timeframe.end')}: {timeframe['end']}", width=13).grid(row=0, column=2, sticky="w", padx=(0, 2))
            # ttk.Label(row_frame, text=" ", width=1).grid(row=0, column=3, sticky="w", padx=(0, 2))

            edit_btn = ttk.Button(
                row_frame, 
                text=self.lang.get("ui.edit"), 
                width=6,
                command=lambda tf=timeframe: self.edit_timeframe(tf)
            )
            edit_btn.grid(row=0, column=3, sticky="e", padx=(0, 2))
            ToolTip(edit_btn, self.lang.get("ui.edit"))
            
            delete_btn = ttk.Button(
                row_frame, 
                text=self.lang.get("ui.delete"), 
                width=6, 
                command=lambda tf=timeframe: self.delete_timeframe(tf)
            )
            delete_btn.grid(row=0, column=4, sticky="e")
            ToolTip(delete_btn, self.lang.get("ui.delete"))
    
    def build_ui(self):
        self.frm = ttk.Frame(self.root, padding=10)
        self.frm.grid()
        
        row = 0
        # We don't need "Execute" function
        # ttk.Button(self.frm, text=self.lang.get("ui.execute"), command=self.open_json_script).grid(
        #     column=1, row=row, sticky='e', pady=10
        # )
        # row += 1
       
        # File selection buttons
        for idx, reader in enumerate(self.readers):
            label = getattr(reader, "label", reader.__name__)
            ttk.Button(
                self.frm,
                text=self.lang.get("ui.open_the_file", file=label),
                command=lambda cls=reader: self.load_file(cls)
            ).grid(column=0, row=idx + row, columnspan=2, sticky='w', pady=5)

        row += len(self.readers)

        # Label and channel list
        ttk.Label(self.frm, text=self.lang.get("ui.select_channels")).grid(column=0, row=row, columnspan=2, sticky='w', pady=5)
        row += 1
        self.channel_list = tk.Listbox(self.frm, height=8, selectmode=tk.MULTIPLE, width=50)
        self.channel_list.grid(column=0, row=row, columnspan=2, pady=5)
        row += 1
        
        self.add_timeframe_button = ttk.Button(self.frm, text=self.lang.get("ui.add_timeframe"), command=self.open_timeframe_dialog)
        self.add_timeframe_button.grid(
            column=1, row=row, sticky='e', pady=10
        )
        row += 1
        ttk.Label(self.frm, text=self.lang.get("ui.start_of_analysis")).grid(column=0, row=row, sticky='w', pady=5)
        
    
        scroll_container = ttk.Frame(self.frm)
        scroll_container.grid(column=0, row=row, columnspan=2, sticky="w", pady=5)
        
        canvas = tk.Canvas(scroll_container, height=100, width=300, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)

        self.timeframes_frame = ttk.Frame(canvas)
        self.timeframes_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.timeframes_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=False)
        scrollbar.pack(side="right", fill="y")
        
        self.render_timeframes(self.timeframes_frame, self.timeframes)
        row += 1 

        self.crop_enabled = tk.BooleanVar(value=False)
        chk_crop = ttk.Checkbutton(
            self.frm, 
            text=self.lang.get("ui.analyze_fragments"), 
            variable=self.crop_enabled, 
            command=self.toggle_crop_widgets
        )
        chk_crop.grid(column=1, row=row, sticky='w', padx=(0, 10))
        row += 1
        
        self.toggle_crop_widgets()

        ttk.Label(self.frm, text=self.lang.get("ui.analysis_method")).grid(column=0, row=row, sticky='e', pady=5)
        self.analyzer_combo = ttk.Combobox(self.frm, values=[getattr(a, "label", a.__name__) for a in self.analyzers])
    
        if self.analyzers:
            self.analyzer_combo.current(0)
            self.analyzer_combo.grid(column=1, row=row, pady=5)      
        row += 1
        self.method_settings = self.get_default_settings(analys=self.analyzer_combo.get())
        
        self.analyzer_combo.bind("<<ComboboxSelected>>", self.on_analyzer_change)
        

        ttk.Button(self.frm, text=self.lang.get("ui.settings"), command=self.open_settings_dialog).grid(
            column=1, row=row, sticky='e', pady=10
        )
        row += 1
        
        # Checkbox for saving statistics
        self.save_stats = tk.BooleanVar(value=False)
        save_stats_chk = ttk.Checkbutton(
            self.frm,
            text=self.lang.get("ui.save_statistics_to_file"),
            variable=self.save_stats,
            command=self.toggle_stats_widgets  # Handler call
        )
        save_stats_chk.grid(column=1, row=row, sticky='w', padx=(0, 10))
        row += 1

        # Label and path entry field
        ttk.Label(self.frm, text=self.lang.get("ui.file_path")).grid(column=0, row=row, sticky='e', pady=5)
        self.stats_path = tk.StringVar()
        self.stats_entry = ttk.Entry(self.frm, textvariable=self.stats_path, state='disabled')  # Disabled if save_stats is False
        self.stats_entry.grid(column=1, row=row, sticky='w')
        row += 1

        # File selection button
        self.stats_button = ttk.Button(self.frm, text=self.lang.get("ui.choose_save_path"), state='disabled', command=self.choose_stats_path)
        self.stats_button.grid(column=1, row=row, sticky='e', pady=10)
        row += 1
        
         # Checkbox for showing graphs
        self.show_graph = tk.BooleanVar(value=False)
        show_graph_chk = ttk.Checkbutton(
            self.frm,
            text=self.lang.get("ui.show_result_graphs"),
            variable=self.show_graph
        )
        show_graph_chk.grid(column=1, row=row, sticky='w', padx=(0, 10))
        row += 1

        ttk.Button(self.frm, text=self.lang.get("ui.analyze_signal"), command=self.analyze_selected).grid(
            column=1, row=row, sticky='e', pady=10
        )
        
    def on_analyzer_change(self, event):
        selected = self.analyzer_combo.get()
        selected = next((a for a in self.analyzers if getattr(a, "label", a.__name__) == selected), None)
        selected = getattr(selected, "label", None)
           
        # [getattr(a, "label", a.__name__) for a in self.analyzers]
        print(f"анализатор's: {self.analyzers}")
        print(f"Выбран анализатор: {selected}")
        if selected:
            self.method_settings = self.get_default_settings(analys=selected)
        
    def open_timeframe_dialog(self, timeframe=None):
        dialog = TimeframeSettings(data=timeframe, timeframes=self.timeframes)
        dialog.open(self.root)
        result = dialog.get_settings()
        if result:
            self.timeframes.append({**result, 'id': str(uuid.uuid4())})
           
            self.render_timeframes(self.timeframes_frame, self.timeframes)
            
        if len(self.timeframes) > 0:
            self.crop_enabled.set(True)
            self.toggle_crop_widgets()
    
    def edit_timeframe(self, timeframe):
        dialog = TimeframeSettings(data=timeframe, timeframes=self.timeframes)
        dialog.open(self.root)
        result = dialog.get_settings()
        
        if result:
            self.timeframes = [ ({**result, 'id': tf["id"]} if tf["id"] == timeframe["id"] else tf) for tf in self.timeframes]
            self.render_timeframes(self.timeframes_frame, self.timeframes)
            
    def delete_timeframe(self, timeframe):
        print('timeframe =>', timeframe)
        self.timeframes = [tf for tf in self.timeframes if tf["id"] != timeframe["id"]]
        self.render_timeframes(self.timeframes_frame, self.timeframes)
        if len(self.timeframes) == 0:
            self.crop_enabled.set(False)
            self.toggle_crop_widgets()

        
    def toggle_crop_widgets(self):
        value = self.crop_enabled.get()
        state = 'normal' if value else 'disabled'
        for child in self.timeframes_frame.winfo_children():
            try:
                self.add_timeframe_button.configure(state=state)
                for ch in child.winfo_children():
                    ch.configure(state=state)
            except tk.TclError:
                pass  # some widgets (Label for example) does not support 'state'
           
   
        
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
        elif analys == getattr(PSD, 'label', __name__):
            
            dialog = PSDSettings(data=self.method_settings)
            dialog.open(self.root)
            settings = dialog.get_settings()
            if settings:
                self.method_settings = {
                    **settings,
                    'name': 'psd'
                }
        else:
            Logger.warning(self.lang.get("logger.unknown_method", method=analys))
            return
    
    def get_default_settings(self, analys):
        if analys == getattr(STFT, 'label', __name__):
            dialog = STFTSettings()
            settings = dialog.get_settings()
            
            return {
                **settings,
                'name': 'stft'
            }
            
        elif analys == getattr(PSD, 'label', __name__):
            dialog = PSDSettings()
            settings = dialog.get_settings()
            
            return {
                **settings,
                'name': 'psd'
            }
        else:
            Logger.warning(self.lang.get("logger.unknown_method", method=analys))
            return None           
        
    def load_file(self, reader):
        path = reader.load()
        if path:
            self.file_path = path
            self.reader_instance = reader(filepath=self.file_path)
            channels = self.reader_instance.get_channels()
            self.source_program = reader.id
            self.timeframes = []
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
        if crop_enabled:
            # lengths = {}
            for ch in selected_channels:
                length = self.reader_instance.get_signal_length(channel=ch)
                # print(f'for "{ch}" length = {lengths[ch]}')
                
                for timeframe in self.timeframes:
                    if timeframe['end'] > length:
                        messagebox.showwarning(self.lang.get("ui.warning"), self.lang.get("timeframe.length_error", name=timeframe['name'], time=timeframe['end'], max=f"{length:.2f}"))
                        return
            
        # start_time = self.start_time_entry.get()
        # end_time = self.end_time_entry.get()
        
        # if crop_enabled:
            # if not start_time or not end_time:
            #     messagebox.showwarning(self.lang.get("ui.warning"), self.lang.get("ui.crop_time_missing"))
            #     return

            # try:
            #     start_time = float(start_time)
            #     end_time = float(end_time)
            # except ValueError:
            #     messagebox.showwarning(self.lang.get("ui.warning"), self.lang.get("ui.crop_time_invalid"))
            #     return

            # if end_time <= start_time:
            #     messagebox.showwarning(self.lang.get("ui.warning"), self.lang.get("ui.crop_time_order_error"))
            #     return
          
        settings = SignalEngine.generate_settings_obj(
            file_path=self.file_path,
            source_program=self.source_program,
            selected_channels=selected_channels,
            method_settings=self.method_settings,
            crop_enabled=crop_enabled,
            time_frames=self.timeframes,
            # start_time=start_time,
            # end_time=end_time,
            save_stats=self.save_stats.get(),
            stats_path=self.stats_path.get(),
            show_graph=self.show_graph.get()
        )
        
        executor = SignalEngine(settings=settings)
        
        executor.start()

    def run(self):
        self.root.mainloop()
        
        
        # settings ==> {
        #     'source_program': 'dewesoft', 
        #     'channels': ['AI A-1', 'AI A-2', 'AI A-3'], 
        #     'method': {'window': 'hann', 'nperseg': 4096, 'min_freq': 5, 'max_freq': 2000, 'overlap_percent': 50, 'scaling': 'density', 'name': 'psd'}, 
        #     'show_graph': False, 
        #     'files': [
        #         {'file_path': 'C:/Users/user/Desktop/13 11.06/test.dxd', 'time_frames': []}
        #     ], 
        #     'stats_settings': {'save_stats': True, 'output_file_path': 'C:/Users/user/Desktop/13 11.06'}
        #     }
        # settings ==> {
        #     'source_program': 'dewesoft', 
        #     'channels': ['AI A-1', 'AI A-2', 'AI A-3'], 
        #     'method': {'window': 'hann', 'nperseg': 4096, 'min_freq': 5, 'max_freq': 2000, 'overlap_percent': 50, 'min_display_freq': 100, 'name': 'stft'}, 
        #     'show_graph': False, 
        #     'files': [
        #         {'file_path': 'C:/Users/user/Desktop/13 11.06/test.dxd', 'time_frames': []}
        #     ], 
        #     'stats_settings': {'save_stats': True, 'output_file_path': 'C:/Users/user/Desktop/13 11.06'}
        #     }
