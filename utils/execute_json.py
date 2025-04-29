import numpy 
import traceback

# readers
from readers import MeraReader, BaseReader

# analyzers
from analyzers import STFT

# renderer
from ui.plot_renderer import PlotRenderer

# constants
from .constants import MERA, FREQ_FRAMES, WINDOWS

# utils
from utils.helpers import get_filename_without_extension

settings = {
    "output_path": '',
    "source_program": '',
    "channels": ['Zпп', 'Xпп', 'Yпп'],
    "channel_groups": [['Zпп', 'Xпп']],
    "method": {
        "name": 'stft',
        "nperseg": 1,
        "window": 'hann',
        "min_freq": 5,
        "max_freq": 2000,
        "overlap_percent": 50
    },
    "files": [
        {
            "file_path": 'D://Mera//test',
            "time_frames": [
                { "name": "0.3", "start_time": 0, "end_time": 100 }
            ]
        },
        {
            "file_path": 'D://Mera//test',
            "time_frames": [
                { "name": "0.3", "start_time": 0, "end_time": 100 }
            ]
        }
    ]
   
}

class CachedData:
    @staticmethod
    def get_key(file_path: str, channel: str):
        return f"{file_path}_{channel}"
    
    def __init__(self, file_path: str, channel: str, source_program: str, data: any, sampling_rate: float):
        self.key = CachedData.get_key(file_path=file_path, channel=channel)
        
        self.file_path = file_path 
        self.channel = channel 
        self.source_program = source_program 
        self.data = data 
        self.sampling_rate = sampling_rate 
        
        
class JSONExecutor:
    def __init__(self, settings):
        self.settings = settings
        self.cached_data = {}
        self.processed_files = {}
        
        self.logs = []
        
    def log_info(self, message): 
        self.logs.append({'status': 'INFO', 'message': message})
        
    def log_error(self, message): 
        self.logs.append({'status': 'ERROR', 'message': message})
        
    def show_errors(self):
        for log in self.logs:
            if log['status'] == 'ERROR':
                print(log)
        
    def read_mera_file(self, file_path: str, channel: str):
        reader = MeraReader(filepath=file_path)
        sampling_rate = reader.get_sampling_rate(channel)
        data = reader.read_channel(channel)
        
        return data, sampling_rate
    
    def slice_signal(self, signal: any, sampling_rate: float, start_time: float, end_time: float):
        reader = MeraReader()
        return reader.slice_signal(data=signal, sampling_rate=sampling_rate, start_time=start_time, end_time=end_time)
        
    def read_and_cache(self, file_path: str, channel: str, source_program: str):
        key = CachedData.get_key(file_path=file_path, channel=channel)
        if key not in self.cached_data:
            if source_program == MERA.id:
                data, sampling_rate = self.read_mera_file(file_path=file_path, channel=channel)
            else:
                self.log_error(message=f"Неизвестная программа источника: {source_program}")
                return None
            
            self.cached_data[key] = CachedData(
                file_path=file_path, 
                channel=channel, 
                source_program=source_program,
                data=data,
                sampling_rate=sampling_rate
            )
        else:
            self.log_info(message=f"Файл {file_path}, канал {channel} взят из кеша")
            
        return self.cached_data[key]

    def run(self):
        try:
            for file_settings in self.settings.get('files', []):
                file_path = file_settings['file_path']
                time_frames = file_settings.get('time_frames', [])
                print('time_frames ==>', time_frames)
                
                # Получаем настройки: локальные или глобальные
                method_settings = file_settings.get('method', self.settings.get('method'))
                
                channels = file_settings.get('channels', self.settings.get('channels'))
                output_path = file_settings.get('output_path', self.settings.get('output_path'))
                
                source_program = file_settings.get('source_program', self.settings.get('source_program'))
                
                if not source_program:
                    self.log_error(message=f"source_program обязательны. Ошибка в файле: {file_settings}")
                    raise  ValueError("source_program обязателен")
                
                # Проверка обязательных параметров
                if not file_path:
                    self.log_error(message=f"file_path обязательны. Ошибка в файле: {file_settings}")
                    raise  ValueError("file_path обязательны")
                
                for channel in channels:
                    result = self.read_and_cache(file_path=file_path, channel=channel, source_program=source_program)
                    if result is None:
                        continue
                    
                    self.process_file(
                        file_path=file_path,
                        data=result.data,
                        channel=result.channel,
                        sampling_rate=result.sampling_rate,
                        time_frames=time_frames,
                        method_settings=method_settings
                    )  
            
            result =  self.get_results()
            print('result ==>', result)            
        except Exception as e:
            self.show_errors()
                


    def process_file(
        self,
        *,
        file_path,
        data,
        channel,
        sampling_rate,
        time_frames,
        method_settings
    ):
        method_name = method_settings['name']
        nperseg = method_settings.get('nperseg')
        window = method_settings.get('window', WINDOWS['HANNING'])
        min_freq = method_settings.get('min_freq', FREQ_FRAMES['MIN'])
        max_freq = method_settings.get('max_freq', FREQ_FRAMES['MAX'])
        
        if method_name not in self.processed_files:
            self.processed_files[method_name] = {}
        
        key = CachedData.get_key(file_path=file_path, channel=channel)
        if method_name == 'stft':
            stft = STFT(window=window, nperseg=nperseg)
        
            if time_frames and len(time_frames) > 0:
                for time_frame in time_frames:
                    sliced_data = self.slice_signal(signal=data, sampling_rate=sampling_rate, start_time=time_frame['start_time'], end_time=time_frame['end_time']) 
                    result = stft.analyze(signal=sliced_data, sampling_rate=sampling_rate, min_freq=min_freq, max_freq=max_freq)
                    framed_key = f"{key}_{time_frame['start_time']}_{time_frame['end_time']}"
                    self.processed_files[method_name][framed_key] = self.stft_results_handle(stft=stft, file_path=file_path, channel=channel, time_frame=time_frame, freq_frame=(min_freq, max_freq), result=result)
            else:
                result = stft.analyze(signal=data, sampling_rate=sampling_rate, min_freq=min_freq, max_freq=max_freq)
                self.processed_files[method_name][key] = self.stft_results_handle(stft=stft, file_path=file_path, channel=channel, time_frame=None, freq_frame=(min_freq, max_freq), result=result)
                        
        else:
            self.log_error(message=f"Метод обработки {method_name} не реализован.")
        
    def get_results(self):
        return self.processed_files
        
    def stft_results_handle(self, stft, file_path: str, channel: str, time_frame, freq_frame, result):
        frequencies, times, amplitudes = result
        frequency, time, max_amplitudes = stft.find_peak_frequency_time(signal=result)
        reader = MeraReader(filepath=file_path)
        
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
        renderer.set_ylabel(f'Амплитуда {"(" + y_units + ')' if y_units else ""}')
        renderer.set_xlabel('Частота (Гц)')
        renderer.set_description(f"{max_y:.2f} {y_units if y_units else ''} ({max_x:.2f} Гц).\nНа {int(minutes)} мин {int(seconds):02d} сек")
        renderer.set_xlim((freq_frame[0], freq_frame[1]))
        renderer.set_ylim((0, max_y * 1.3))
        summary = f"{max_y:.2f} {y_units if y_units else ''}, {max_x:.2f} Гц"
        
        return renderer, channel, file_path, summary
        
        
    def render_graphs(self, results, settings):
        # цикл по настройкам
        # рендер результатов
        
        


