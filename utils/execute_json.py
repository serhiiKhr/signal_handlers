import numpy 
import traceback
import uuid

# readers
from readers import MeraReader, BaseReader

# analyzers
from analyzers import STFT

# renderer
from ui.plot_renderer import PlotRenderer

# constants
from .constants import MERA, FREQ_FRAMES, WINDOWS, DEFAULT_IMG_EXTENSION

# utils
from utils.helpers import get_filename_without_extension, group_by, find_index, deep_get, get_file_path, ensure_path_from_parts

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
        self.assign_ids(self.settings)
        
        self.cached_data = {}
        self.processed_files = {}
        self.logs = []
        
    def log_info(self, message): 
        if isinstance(message, list):
            for msg in message:
                self.logs.append({'status': 'INFO', 'message': msg})
        else:
            self.logs.append({'status': 'INFO', 'message': message})
        
    def log_error(self, message): 
        if isinstance(message, list):
            for msg in message:
                self.logs.append({'status': 'ERROR', 'message': msg})
        else:
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
        errors = self.validate_settings(self.settings)
        if len(errors) > 0:
            self.log_error(errors)
            return
            
        try:
            for file_settings in self.settings.get('files', []):
                id = file_settings['id']
                settings = self.get_settings_by_id(settings=self.settings, target_id=id)
                if not settings:
                    return
                
                file_path = settings["file_path"]
                time_frames = settings["time_frames"]
                channels = settings["channels"]
                method = settings["method"]
                source_program = settings["source_program"]     
                
                if not source_program:
                    self.log_error(message=f"source_program обязательны. Ошибка в файле: {file_settings}")
                    raise ValueError("source_program обязателен")
                
                # Проверка обязательных параметров
                if not file_path:
                    self.log_error(message=f"file_path обязательны. Ошибка в файле: {file_settings}")
                    raise  ValueError("file_path обязательны")
                
                if len(time_frames) > 0:
                    for tf in time_frames:
                        self.process_file(
                            source_program=source_program,
                            id=id,
                            file_path=file_path,
                            channels=channels,
                            time_frame=tf,
                            method=method
                        )
                else:
                    self.process_file(
                        source_program=source_program,
                        id=id,
                        file_path=file_path,
                        channels=channels,
                        method=method
                    )
                    
            results =  self.get_results()
            self.render_graphs(results=results, settings=self.settings)       
        except Exception as e:
            self.show_errors()  

    def process_file(
        self,
        *,
        source_program,
        id,
        file_path,
        channels,
        time_frame=None,
        method
    ):
        method_name = method['name']
        
        if method_name not in self.processed_files:
            self.processed_files[method_name] = {}
            
        for channel in channels:
            cached = self.read_and_cache(file_path=file_path, channel=channel, source_program=source_program)
            if cached is None:
                continue
            data = cached.data
            sampling_rate  = cached.sampling_rate 
    
            key = f"{id}___{channel}"
            if method_name == 'stft':
                nperseg = method.get('nperseg')
                window = method.get('window', WINDOWS['HANNING'])
                min_freq = method.get('min_freq', FREQ_FRAMES['MIN'])
                max_freq = method.get('max_freq', FREQ_FRAMES['MAX'])
                min_display_freq = method.get('min_display_freq', None)
                
                stft = STFT(window=window, nperseg=nperseg)
                if time_frame:
                    sliced_data = self.slice_signal(signal=data, sampling_rate=sampling_rate, start_time=time_frame['start_time'], end_time=time_frame['end_time']) 
                    result = stft.analyze(signal=sliced_data, sampling_rate=sampling_rate, min_freq=min_freq, max_freq=max_freq)
                    framed_key = f"{key}___{time_frame['id']}"
                    renderer, summary = self.stft_results_handle(stft=stft, file_path=file_path, channel=channel, time_frame=time_frame, freq_frame=(min_freq, max_freq), result=result, min_display_freq=min_display_freq)
                    self.processed_files[method_name][framed_key] = {
                        'renderer': renderer,
                        'summary': summary,
                        'channel': channel,
                        'id': id,
                        'tf_id': time_frame['id']
                    }
                else:
                    result = stft.analyze(signal=data, sampling_rate=sampling_rate, min_freq=min_freq, max_freq=max_freq)
                    renderer, summary = self.stft_results_handle(stft=stft, file_path=file_path, channel=channel, time_frame=None, freq_frame=(min_freq, max_freq), result=result)
                    self.processed_files[method_name][key] = {
                        'renderer': renderer,
                        'summary': summary,
                        'channel': channel,
                        'id': id
                    }
            else:
                self.log_error(message=f"Метод обработки {method_name} не реализован.")
        
    def get_results(self):
        return self.processed_files
        
    def stft_results_handle(self, stft, file_path: str, channel: str, time_frame, freq_frame, result, min_display_freq):
        frequencies, times, amplitudes = result
        frequency, time, max_amplitudes = stft.find_peak_frequency_time(signal=result, min_frequency=min_display_freq)
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
        
        return renderer, summary
        
    def render_graphs(self, results, settings):
        groupped = {}
        for method_name in results.keys():
            groupped[method_name] = group_by(results[method_name], 'id')
        
        for method_name in groupped:
            for id in groupped[method_name]:
                file_settings = self.get_settings_by_id(settings=settings, target_id=id)
                channel_groups = deep_get(file_settings, ['groups_settings', 'groups'], [])
                single_image_group = deep_get(file_settings, ['groups_settings', 'single_image_group'], False)
                
                file_settings = self.get_settings_by_id(settings=settings, target_id=id)
                file_name = get_filename_without_extension(file_settings['file_path'])
                path_arr = [file_settings['output_path'], method_name, file_name]
                time_frames_name = deep_get(file_settings, ['time_frames', 0, 'name'], '')
                
                if time_frames_name:
                    path_arr.append(time_frames_name)
                    
                if len(channel_groups) > 0:
                    for channel_group in channel_groups:
                        grouped_channels = []
                        for i, ch in enumerate(channel_group):
                            ch_result_index = find_index(groupped[method_name][id], lambda v: v['channel'] == ch)
                            if ch_result_index >= 0:
                                grouped_channels.append(groupped[method_name][id][ch_result_index]['renderer'])
                            else:
                                self.log_error(f"Нет канала {ch} в списке результатов вычисления")
                                                        
                        valid_path = ensure_path_from_parts(path_arr)
                        group_file_name = "_".join(channel_group)
                        
                        
                        if single_image_group:
                            PlotRenderer.save_multiple_on_single_plot(plots=grouped_channels, path=valid_path + f"//{group_file_name}{DEFAULT_IMG_EXTENSION}")
                        else:
                            PlotRenderer.save_multiply(plots=grouped_channels, path=valid_path + f"//{group_file_name}{DEFAULT_IMG_EXTENSION}")

                else:
                    "save by one file"
                    for result in groupped[method_name][id]:
                        
                        renderer = result['renderer']
                        channel = result['channel']
                        
                        if 'tf_id' in result:
                            timeframe_settings = self.get_timeframe_settings_by_id(settings=settings, target_id=result['tf_id'])
                            path_arr.append(timeframe_settings['name'])
                            
                        valid_path = ensure_path_from_parts(path_arr)
                        renderer.save(path=valid_path + f"//{channel}{DEFAULT_IMG_EXTENSION}")        
        
    def validate_settings(self, settings):
        errors = []

        def log(msg):
            errors.append(msg)

        global_channels = settings.get('channels')
        global_source_program = settings.get('source_program')
        global_method = settings.get('method')

        if not isinstance(global_method, dict) or 'name' not in global_method:
            log("Глобальные настройки 'method' должны содержать параметр 'name'.")

        files = settings.get('files')
        if not isinstance(files, list):
            log("'files' должен быть списком.")
            return errors

        # Проверка на 'groups_settings'
        groups_settings = settings.get('groups_settings', {})
        if 'groups' in groups_settings:
            groups = groups_settings['groups']
            if not isinstance(groups, list):
                log("'groups' должен быть списком.")
            else:
                for i, group in enumerate(groups):
                    if not isinstance(group, list):
                        log(f"'groups[{i}]' должно быть списком.")
                    else:
                        for ch in group:
                            if not isinstance(ch, str):
                                log(f"В 'groups[{i}]' все элементы должны быть строками (каналами).")
        if 'single_image_group' in groups_settings and not isinstance(groups_settings['single_image_group'], bool):
            log("'single_image_group' должен быть булевым значением.")

        for i, file in enumerate(files):
            file_path = file.get('file_path')
            if not file_path:
                log(f"[Файл {i}] Отсутствует обязательный параметр 'file_path'.")

            method = file.get('method', global_method)
            if not method or not isinstance(method, dict) or 'name' not in method:
                log(f"[Файл {i}] Настройки 'method' отсутствуют или не содержат обязательный параметр 'name'.")

            channels = file.get('channels', global_channels)
            if not channels:
                log(f"[Файл {i}] Не указаны каналы: ни в файле, ни глобально.")

            source_program = file.get('source_program', global_source_program)
            if not source_program:
                log(f"[Файл {i}] Не указан 'source_program': ни в файле, ни глобально.")

            time_frames = file.get('time_frames', [])
            if not isinstance(time_frames, list):
                log(f"[Файл {i}] 'time_frames' должен быть списком.")
            else:
                for j, frame in enumerate(time_frames):
                    if not isinstance(frame, dict):
                        log(f"[Файл {i}] time_frames[{j}] должен быть словарём.")
                        continue
                    for field in ['name', 'start_time', 'end_time']:
                        if field not in frame:
                            log(f"[Файл {i}] time_frames[{j}] отсутствует обязательное поле '{field}'.")

        return errors
    
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
            # Проверка ID самого файла
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

        self.log_error(f"ID '{target_id}' не найден в файлах или time_frames")
        return None
    
    def get_timeframe_settings_by_id(self, settings: dict, target_id: str):
        for file in settings.get("files", []):
            for frame in file.get("time_frames", []):
                if frame.get("id") == target_id:
                    file_settings = self.get_settings_by_id(settings=settings, target_id=file['id'])
                    
                    return {**file_settings, **frame}
        return None
        
    def assign_ids(self, settings: dict) -> None:
        for file_settings in settings.get("files", []):
            # Добавить id файлу, если его нет
            if "id" not in file_settings:
                file_settings["id"] = str(uuid.uuid4())

            # Добавить id каждому time_frame, если они есть
            time_frames = file_settings.get("time_frames", [])
            for tf in time_frames:
                if "id" not in tf:
                    tf["id"] = str(uuid.uuid4())


