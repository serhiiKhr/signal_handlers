import numpy

from utils.language_manager import LanguageManager
from utils.logger import Logger
from utils.helpers import get_file_path, get_filename_without_extension, group_by, deep_get, find_index, ensure_path_from_parts, get_file_path
from utils.csv_creator import save_data_to_csv

from ui.plot_renderer import PlotRenderer

# analyzers
from analyzers import STFT, BaseAnalyzer

# readers
from readers import MeraReader, DWReader, BaseReader

# constants
from utils.constants import MERA, DEWESOFT, FREQ_FRAMES, WINDOWS, DEFAULT_IMG_EXTENSION

class BaseHandler:
    def __init__(self):
        self.lang = LanguageManager()
        self.results = []
        self.settings = {}
        self.summary = {}
        
    @staticmethod
    def get_file_reader(source_program: str, file_path: str):
        if source_program == MERA.id:
            return MeraReader(filepath=file_path)
        elif source_program == DEWESOFT.id:
            return DWReader(filepath=file_path)
        # NOTE: add file reader checking here
        # elif source_program == DEWESOFT.id:
        #     self.file_reader = DWReader(filepath=file_path)
        else:
            return BaseReader()
    
    def get_summary(self):
        return self.summary
        
    def get_settings_by_id(self, settings: dict, target_id: str) -> dict:
    
        global_settings = {
            "output_path": settings.get("output_path"),
            "channels": settings.get("channels"),
            "groups_settings": settings.get("groups_settings"),
            "method": settings.get("method"),
            "source_program": settings.get("source_program"),
            "show_graph": settings.get("show_graph", False),
            "save_stats": deep_get(settings, ['stats_settings', 'save_stats'], False),
            "output_file_path": deep_get(settings, ['stats_settings', 'output_file_path'], '')
        }        

        for file_settings in settings.get("files", []):
            file_id = file_settings.get("id")
            file_path = file_settings.get("file_path")
            time_frames = file_settings.get("time_frames", [])
            # Check the ID of the file
            if file_id == target_id:
                output_path = file_settings.get("output_path", global_settings["output_path"])
                stats_settings = file_settings.get('stats_settings', {})
                stats_output_file_path = stats_settings.get('output_file_path', '')
                if not output_path:
                    output_path = get_file_path(file_settings.get("file_path"))
                return {
                    "file_path": file_path,
                    "time_frames": time_frames,
                    "output_path": output_path,
                    "channels": file_settings.get("channels", global_settings["channels"]),
                    "groups_settings": file_settings.get("groups_settings", global_settings["groups_settings"]),
                    "method": file_settings.get("method", global_settings["method"]),
                    "source_program": file_settings.get("source_program", global_settings["source_program"]),
                    "show_graph": global_settings["show_graph"] if 'show_graph' not in file_settings else file_settings.get("show_graph"),
                    "save_stats": global_settings["save_stats"] if 'save_stats' not in stats_settings else stats_settings.get("save_stats"),
                    "output_file_path": stats_output_file_path or global_settings['output_file_path'] or get_file_path(file_path),
                    
                }

        Logger.error(self.lang.get("logger.target_id_not_found", target_id=target_id))
        return None
    
    def get_timeframe_settings_by_id(self, settings: dict, target_id: str):
        for file in settings.get("files", []):
            for frame in file.get("time_frames", []):
                if frame.get("id") == target_id:
                    file_settings = self.get_settings_by_id(settings=settings, target_id=file['id'])
                    
                    return {**file_settings, **frame}
                
        Logger.error(self.lang.get("logger.target_id_not_found", target_id=target_id))
        return None

class STFTHandler(BaseHandler):
    def __init__(
        self, 
        id: str = '',
        settings: dict = None
    ):
        super().__init__()
        
        # validate during class instance creation
        if not id or settings is None:
            error = self.lang.get("stft.stft_missing_required_parameters")
            Logger.error(error)
            raise ValueError(error)
        
        self.id = id
        self.settings = self.get_settings_by_id(settings=settings, target_id=self.id)
        
        source_program = deep_get(settings, ['source_program'], '')
        file_path = deep_get(settings, ['file_path'], '')
        
        window = deep_get(self.settings, ['method', 'window'], None)
        nperseg = deep_get(self.settings, ['method', 'nperseg'], None)
        
        self.analyzer = STFT(window=window, nperseg=nperseg)
        
        self.file_reader = BaseHandler.get_file_reader(source_program=source_program, file_path=file_path)
        
        
        
    def run(self, signals=None):
        
        channels = deep_get(self.settings, ['channels'], [])
        time_frames = deep_get(self.settings, ['time_frames'], None)
        file_path = deep_get(self.settings, ['file_path'], '')
        source_program = deep_get(self.settings, ['source_program'], '')
        file_name = get_filename_without_extension(file_path)
       
        min_freq = deep_get(self.settings, ['method', 'min_freq'], FREQ_FRAMES['MIN'])
        max_freq = deep_get(self.settings, ['method', 'max_freq'], FREQ_FRAMES['MAX'])
        min_display_freq = deep_get(self.settings, ['method', 'min_display_freq'], None)
        
        save_stats = deep_get(self.settings, ['save_stats'], False)
        output_file_path = deep_get(self.settings, ['output_file_path'], '')
        
        self.file_reader = BaseHandler.get_file_reader(source_program=source_program, file_path=file_path)    
            
        for channel in channels:
            channel_signal = deep_get(signals, [channel], (None, None))
            if channel_signal:
                signal = channel_signal.data
                sampling_rate = channel_signal.sampling_rate
            else:
                # todo: add to i18n
                Logger.error(f'no channel ({channel}) in signals')
                return

            if time_frames is not None and (isinstance(time_frames, list) and len(time_frames) > 0):
                for time_frame in time_frames:
                    
                    sliced_data = self.file_reader.slice_signal(data=signal, sampling_rate=sampling_rate, start_time=time_frame['start_time'], end_time=time_frame['end_time'])
                    result = self.analyzer.analyze(signal=sliced_data, sampling_rate=sampling_rate, min_freq=min_freq, max_freq=max_freq)
                    
                    renderer, summary = self.handle(
                        file_path=file_path, 
                        channel=channel, 
                        time_frame=time_frame, 
                        freq_frame=(min_freq, max_freq), 
                        result=result, 
                        min_display_freq=min_display_freq
                    )
                    self.results.append({
                        'renderer': renderer,
                        'summary': summary,
                        'channel': channel,
                        'id': self.id,
                        'tf_id': time_frame['id']
                    })
                    summare_name = f"{file_name} {time_frame['name']}"
                    if summare_name not in self.summary:
                        self.summary[summare_name] = {}
                        self.summary[summare_name]['save_stats'] = save_stats
                        self.summary[summare_name]['output_file_path'] = output_file_path
                        self.summary[summare_name]['channels'] = []
                    self.summary[summare_name]['channels'].append({'channel': channel, 'summary': summary})
            else:
                result = self.analyzer.analyze(signal=signal, sampling_rate=sampling_rate, min_freq=min_freq, max_freq=max_freq)
                renderer, summary = self.handle(
                    file_path=file_path, 
                    channel=channel, 
                    time_frame=None, 
                    freq_frame=(min_freq, max_freq), 
                    result=result, 
                    min_display_freq=min_display_freq
                )
                self.results.append({
                    'renderer': renderer,
                    'summary': summary,
                    'channel': channel,
                    'id': self.id
                })
                summare_name = f"{file_name}"
                if summare_name not in self.summary:
                    self.summary[summare_name] = {}
                    self.summary[summare_name]['save_stats'] = save_stats
                    self.summary[summare_name]['output_file_path'] = output_file_path
                    self.summary[summare_name]['channels'] = []
                self.summary[summare_name]['channels'].append({'channel': channel, 'summary': summary})
        
    def handle(self, file_path: str, channel: str, time_frame, freq_frame, result, min_display_freq):
        frequencies, times, amplitudes = result
        frequency, time, max_amplitudes = self.analyzer.find_peak_frequency_time(signal=result, min_frequency=min_display_freq)
        
        file_name = get_filename_without_extension(file_path)
        
        renderer = PlotRenderer(xdata=frequencies, ydata=max_amplitudes)
        max_idx = numpy.argmax(max_amplitudes)
        max_x = frequencies[max_idx]
        max_y = max_amplitudes[max_idx]
        
        if time_frame is not None:
            time = time + time_frame.get('start_time', 0)
            
        minutes = time // 60
        seconds = time % 60
        
        renderer.set_peaks([{'x': max_x, 'y': max_y}])
        
        renderer.set_title(f"{file_name} ({channel})")
        y_units = self.file_reader.get_y_units(channel=channel)
        y_label_text = self.lang.get("ui.amplitude")
        y_label_text += f"({y_units})" if y_units else ""    
        renderer.set_ylabel(y_label_text)
        
        hz = self.lang.get("ui.hz")
        x_label_text = f"{self.lang.get("ui.frequency")} ({self.lang.get("ui.hz")})"
        renderer.set_xlabel(x_label_text)
        formatted_time = self.lang.get("plot.formatted_time", min=f"{int(minutes)}", sec=f"{int(seconds):02d}")
        renderer.set_description(f"{max_y:.2f} {y_units if y_units else ''} ({max_x:.2f} {hz}).\n{formatted_time}")
        renderer.set_xlim((freq_frame[0], freq_frame[1]))
        renderer.set_ylim((0, max_y * 1.3))
        summary = f"{max_y:.2f}{' ' + y_units if y_units else ''}, {max_x:.2f} {hz}"
        
        return renderer, summary
    
    def render_graphs(self):
        groupped = group_by(self.results, 'id')
        
        for id in groupped.keys():
            method_name = deep_get(self.settings, ['method', 'name'], '')
            channel_groups = deep_get(self.settings, ['groups_settings', 'groups'], [])
            single_image_group = deep_get(self.settings, ['groups_settings', 'single_image_group'], False)
            show_graph = deep_get(self.settings, ['show_graph'], False)
            
            file_name = get_filename_without_extension(self.settings['file_path'])
            
            path_arr = []
            output_path = deep_get(self.settings, ['output_path'], '')
            if output_path:
                path_arr.append(output_path)
                
            path_arr.append(method_name)
            path_arr.append(file_name)
            
            
            time_frames_name = deep_get(self.settings, ['time_frames', 0, 'name'], '')
            
            if time_frames_name:
                path_arr.append(time_frames_name)
                
            if len(channel_groups) > 0:
                for channel_group in channel_groups:
                    grouped_channels = []
                    for i, ch in enumerate(channel_group):
                        ch_result_index = find_index(groupped[id], lambda v: v['channel'] == ch)
                        if ch_result_index >= 0:
                            grouped_channels.append(groupped[id][ch_result_index]['renderer'])
                        else:
                            Logger.error(self.lang.get("logger.no_channel_in_computation_results", channel=ch))
                                                    
                    valid_path = ensure_path_from_parts(path_arr)
                    group_file_name = "_".join(channel_group)
                    
                    if single_image_group:
                        PlotRenderer.save_multiple_on_single_plot(plots=grouped_channels, show_graph=show_graph, path=valid_path + f"//{group_file_name}{DEFAULT_IMG_EXTENSION}")
                    else:
                        PlotRenderer.save_multiply(plots=grouped_channels, show_graph=show_graph, path=valid_path + f"//{group_file_name}{DEFAULT_IMG_EXTENSION}")

            else:
                "save by one file"
                for result in groupped[id]:
                    
                    renderer = result['renderer']
                    channel = result['channel']
                    
                    if 'tf_id' in result:
                        timeframe_settings = self.get_timeframe_settings_by_id(settings=self.settings, target_id=result['tf_id'])
                        path_arr.append(timeframe_settings['name'])
                        
                    valid_path = ensure_path_from_parts(path_arr)
                    renderer.save(path=valid_path + f"//{channel}{DEFAULT_IMG_EXTENSION}")
                    if show_graph:
                        renderer.show()
            
        
    
    