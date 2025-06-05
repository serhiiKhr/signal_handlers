import uuid
import traceback
from datetime import datetime

# utils
from utils.helpers import deep_get, group_by, get_file_path
from utils.csv_creator import save_data_to_csv

from utils.language_manager import LanguageManager
from utils.logger import Logger

from .cached_data import CachedData
from .methods_handlers import BaseHandler, STFTHandler

class SignalEngine:
    def __init__(self, settings):
        self.settings = settings
        self.assign_ids(self.settings)
        
        self.lang = LanguageManager()
        self.cached_data = {}
        self.handled_files = {}
        self.summary = {}
        
    def log_info(self, message): 
        if isinstance(message, list):
            for msg in message:
                Logger.info(msg)
        else:
            Logger.info(message)
            
    def log_error(self, message): 
        if isinstance(message, list):
            for msg in message:
                Logger.error(msg)
        else:
            Logger.error(message)
            
    def read_file(self, source_program: str, file_path: str, channel: str):
        try:
            reader = BaseHandler.get_file_reader(file_path=file_path, source_program=source_program)
            sampling_rate = reader.get_sampling_rate(channel)
            data = reader.read_channel(channel)
            return data, sampling_rate
        except Exception as e:
            self.log_error(message=str(e))
            self.log_error(message=self.lang.get("logger.unknown_source_program", source_program=source_program))
            return None, None
        
    def read_and_cache(self, file_path: str, channel: str, source_program: str):
        key = CachedData.get_key(file_path=file_path, channel=channel)
         
        if key not in self.cached_data:
            data, sampling_rate = self.read_file(source_program=source_program, file_path=file_path, channel=channel)

            if data is None or sampling_rate is None:
                return
            
            self.cached_data[key] = CachedData(
                file_path=file_path, 
                channel=channel, 
                source_program=source_program,
                data=data,
                sampling_rate=sampling_rate
            )
        else:
            self.log_info(message=self.lang.get("logger.file_from_cache", file_path=file_path, channel=channel))
            
        return self.cached_data[key]
    
    def start(self):
        # validation
        errors = self.validate_settings_obj(self.settings)
        if len(errors) > 0:
            self.log_error(errors)
            return
        
        try:
            # get files_settings
            files_settings = self.settings.get('files', [])
            # get file_settings
            for file_settings in files_settings:
                # get setting id
                id = file_settings['id']
                self.handle_file(id=id, settings=self.settings)
                
            self.log_results_to_csv()
                
        except Exception as e:
            self.log_error(message=str(e))
            traceback.format_exc()
            
    def handle_file(self, id: str = '', settings: dict = None):
        baseHandler = BaseHandler()
        # get settings by id
        file_settings = baseHandler.get_settings_by_id(settings=settings, target_id=id)
        # get file path 
        file_path = deep_get(file_settings, ['file_path'], '')
        source_program = deep_get(file_settings, ['source_program'], '')
        channels = deep_get(file_settings, ['channels'], [])
        
        cached_data = {}
        # cache data from file
        for channel in channels:
            cached_data[channel] = self.read_and_cache(file_path=file_path, channel=channel, source_program=source_program)
        # now data are cached
        
        # get handle method name
        method_name = deep_get(file_settings, ['method', 'name'], '')
        if method_name == 'stft':
            # handle it
            handler = STFTHandler(id=id, settings=settings)
            handler.run(signals=cached_data)
            handler.render_graphs()
            self.summary = {**self.summary, **handler.get_summary()}
        else:
            self.log_error(message=self.lang.get("logger.method_not_implemented", method_name=method_name))
            return
        
    def validate_settings_obj(self, settings):
        errors = []

        def log(msg):
            errors.append(msg)

        global_channels = settings.get('channels')
        global_source_program = settings.get('source_program')
        global_method = settings.get('method')
        global_show_graph = settings.get('show_graph')

        if global_show_graph is not None and not isinstance(global_show_graph, bool):
            log(self.lang.get("logger.prop_must_be_boolean", prop_name="show_graph"))

        if not isinstance(global_method, dict) or 'name' not in global_method:
            log(self.lang.get("logger.global_settings_error", method="method", name="name"))

        files = settings.get('files')
        if not isinstance(files, list):
            log(self.lang.get("logger.must_be_list", prop_name="files"))
            return errors

        # groups_settings
        groups_settings = settings.get('groups_settings', {})
        if 'groups' in groups_settings:
            groups = groups_settings['groups']
            if not isinstance(groups, list):
                log(self.lang.get("logger.must_be_list", prop_name="groups"))
            else:
                for i, group in enumerate(groups):
                    if not isinstance(group, list):
                        log(self.lang.get("logger.must_be_list", prop_name=f"groups[{i}]"))
                    else:
                        for ch in group:
                            if not isinstance(ch, str):
                                log(self.lang.get("logger.all_elements_must_be_strings", prop_name=f"groups[{i}]"))

        if 'single_image_group' in groups_settings and not isinstance(groups_settings['single_image_group'], bool):
            log(self.lang.get("logger.prop_must_be_boolean", prop_name="single_image_group"))

        # stats_settings
        stats_settings = settings.get('stats_settings')
        if stats_settings is not None:
            if not isinstance(stats_settings, dict):
                log(self.lang.get("logger.must_be_dict", prop_name="stats_settings"))
            else:
                if 'save_stats' in stats_settings and not isinstance(stats_settings['save_stats'], bool):
                    log(self.lang.get("logger.prop_must_be_boolean", prop_name="stats_settings.save_stats"))
                if 'output_file_path' in stats_settings and not isinstance(stats_settings['output_file_path'], str):
                    log(self.lang.get("logger.prop_must_be_string", prop_name="stats_settings.output_file_path"))

        for i, file in enumerate(files):
            file_path = file.get('file_path')
            if not file_path:
                log(self.lang.get("logger.missing_file_path", file_index=i))

            method = file.get('method', global_method)
            if not method or not isinstance(method, dict) or 'name' not in method:
                log(self.lang.get("logger.missing_method_name", file_index=i))

            channels = file.get('channels', global_channels)
            if not channels:
                log(self.lang.get("logger.missing_channels", file_index=i))

            source_program = file.get('source_program', global_source_program)
            if not source_program:
                log(self.lang.get("logger.missing_source_program", file_index=i))

            show_graph = file.get('show_graph', global_show_graph)
            if show_graph is not None and not isinstance(show_graph, bool):
                log(self.lang.get("logger.prop_must_be_boolean", prop_name=f"files[{i}].show_graph"))

            time_frames = file.get('time_frames', [])
            if not isinstance(time_frames, list):
                log(self.lang.get("logger.missing_time_frames_list", file_index=i))
            else:
                for j, frame in enumerate(time_frames):
                    if not isinstance(frame, dict):
                        log(self.lang.get("logger.time_frames_not_dict", file_index=i, time_frame_index=j))
                        continue
                    for field in ['name', 'start_time', 'end_time']:
                        if field not in frame:
                            log(self.lang.get("logger.missing_field_in_time_frame", file_index=i, time_frame_index=j, field=field))

        return errors
    
    @staticmethod
    def generate_settings_obj(**kwargs):
        # save_stats, 
        # show_graph, 
        # stats_path, 
        # source_program, 
        # selected_channels, 
        # method_settings, 
        # file_path, 
        # crop_enabled, 
        # start_time, 
        # end_time

        # global settings
        settings = {
            "source_program": kwargs.get("source_program"),
            "channels": kwargs.get("selected_channels", []),
            "method": kwargs.get("method_settings", {}),
            "show_graph": kwargs.get("show_graph", False),
            "files": [],
        }
       
        file_path = kwargs.get("file_path")
        crop_enabled = kwargs.get("crop_enabled", False)
        time_frames = kwargs.get("time_frames", [])
        # start_time = kwargs.get("start_time", 0)
        # end_time = kwargs.get("end_time", 0)
        
        file_settings = {"file_path": file_path, "time_frames": []}
        if crop_enabled:
            for tf in time_frames:    
                file_settings["time_frames"].append({
                    "name": tf['name'],
                    "start_time": tf['start'],
                    "end_time": tf['end']
                })
        settings["files"].append(file_settings)

        if kwargs.get("save_stats", False):
            output_file_path = kwargs.get("stats_path") or get_file_path(file_path)
            settings["stats_settings"] = {
                "save_stats": True,
                "output_file_path": output_file_path
            }
            
            
        return settings
    
    def log_results_to_csv(self):
        datarow = []
        for key in self.summary.keys():
            if not self.summary[key]['save_stats']:
                continue
            
            data = {
                'filename': key,
                'output_file_path': self.summary[key]['output_file_path']
            }
            for ch in self.summary[key]['channels']:
                data[ch['channel']] = ch['summary']
            datarow.append(data)
            
        groupped = group_by(datarow, 'output_file_path')
        filtered = {
            key: [
                {k: v for k, v in item.items() if k != 'output_file_path'}
                for item in items
            ]
            for key, items in groupped.items()
        }
        for path in filtered.keys():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_data_to_csv(f"{path}\\{timestamp}.csv", filtered[path])
        
    
    def assign_ids(self, settings: dict) -> None:
        for file_settings in settings.get("files", []):
            # Add an ID to the file if it's missing
            if "id" not in file_settings:
                file_settings["id"] = str(uuid.uuid4())

            # Add an ID to each time_frame if they exist
            time_frames = file_settings.get("time_frames", [])
            for tf in time_frames:
                if "id" not in tf:
                    tf["id"] = str(uuid.uuid4())