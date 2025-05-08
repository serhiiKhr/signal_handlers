import numpy

from utils.language_manager import LanguageManager
from utils.logger import Logger
from utils.helpers import get_file_path, get_filename_without_extension

from ui.plot_renderer import PlotRenderer

# analyzers
from analyzers import STFT, BaseAnalyzer

# readers
from readers import MeraReader, DWReader, BaseReader

# constants
from utils.constants import MERA, FREQ_FRAMES, WINDOWS, DEFAULT_IMG_EXTENSION

class BaseHandler:
    def __init__(self):
        self.lang = LanguageManager()
        
    def get_settings_by_id(self, settings: dict, target_id: str) -> dict:
    
        global_settings = {
            "output_path": settings.get("output_path"),
            "channels": settings.get("channels"),
            "groups_settings": settings.get("groups_settings"),
            "method": settings.get("method"),
            "source_program": settings.get("source_program")
        }        

        for file_settings in settings.get("files", []):
            file_id = file_settings.get("id")
            file_path = file_settings.get("file_path")
            time_frames = file_settings.get("time_frames", [])
            # Check the ID of the file
            if file_id == target_id:
                output_path = file_settings.get("output_path", global_settings["output_path"])
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
        key='',
        time_frames=None,
        method_settings=None,
        channel=None,
        data=None,
        sampling_rate=None
    ):
        self.lang = LanguageManager()
        if not key or time_frames is None or method_settings or channel is None:
            error = self.lang.get("stft.stft_missing_required_parameters")
            Logger.error(error)
            raise ValueError(error)
        
        nperseg = method_settings.get('nperseg')
        window = method_settings.get('window', WINDOWS['HANNING'])
        self.analyzer: BaseAnalyzer = STFT(window=window, nperseg=nperseg)
        
        self.run(
            key=key, 
            signal=data, 
            sampling_rate=sampling_rate, 
            method_settings=method_settings,
            time_frames=time_frames
        )
        
        self.results = {}
        
    def run(self, key='', signal=None, sampling_rate=None, method_settings=None, channels=None, time_frames=None):
        for channel in channels:
            
            min_freq = method_settings.get('min_freq', FREQ_FRAMES['MIN'])
            max_freq = method_settings.get('max_freq', FREQ_FRAMES['MAX'])
            min_display_freq = method_settings.get('min_display_freq', None)
            
            if time_frames is not None and isinstance(time_frames, list):
                for time_frame in time_frames:
                    sliced_data = self.slice_signal(signal=signal, sampling_rate=sampling_rate, start_time=time_frame['start_time'], end_time=time_frame['end_time']) 
                    result = self.analyzer.analyze(signal=sliced_data, sampling_rate=sampling_rate, min_freq=min_freq, max_freq=max_freq)
                    framed_key = f"{key}___{time_frame['id']}"
                    renderer, summary = self.stft_results_handle(stft=stft, file_path=file_path, channel=channel, time_frame=time_frame, freq_frame=(min_freq, max_freq), result=result, min_display_freq=min_display_freq)
                    self.results[framed_key] = {
                        'renderer': renderer,
                        'summary': summary,
                        'channel': channel,
                        'id': id,
                        'tf_id': time_frame['id']
                    }
            else:
                result = self.analyzer.analyze(signal=signal, sampling_rate=sampling_rate, min_freq=min_freq, max_freq=max_freq)
                renderer, summary = self.handle(file_path=file_path, channel=channel, time_frame=None, freq_frame=(min_freq, max_freq), result=result)
                self.results[key] = {
                    'renderer': renderer,
                    'summary': summary,
                    'channel': channel,
                    'id': id
                }
        else:
            result = self.analyzer.analyze(signal=signal, sampling_rate=sampling_rate, min_freq=min_freq, max_freq=max_freq)
            renderer, summary = self.handle(file_path=file_path, channel=channel, time_frame=None, freq_frame=(min_freq, max_freq), result=result)
            self.results[key] = {
                'renderer': renderer,
                'summary': summary,
                'channel': channel,
                'id': id
            }
        
    def handle(self, file_path: str, channel: str, time_frame, freq_frame, result, min_display_freq):
        frequencies, times, amplitudes = result
        frequency, time, max_amplitudes = self.analyzer.find_peak_frequency_time(signal=result, min_frequency=min_display_freq)
        reader: BaseReader =  MeraReader(filepath=file_path)
        
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
        y_units = reader.get_y_units(channel=channel)
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
        summary = f"{max_y:.2f} {y_units if y_units else ''}, {max_x:.2f} {hz}"
        
        return renderer, summary
        
    
    