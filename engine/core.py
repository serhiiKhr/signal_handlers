
import numpy 
import uuid

# readers
from readers import MeraReader, BaseReader

# utils
from utils.helpers import get_filename_without_extension, group_by, find_index, deep_get, get_file_path, ensure_path_from_parts

from utils.language_manager import LanguageManager
from utils.logger import Logger
# constants
from utils.constants import MERA, FREQ_FRAMES, WINDOWS, DEFAULT_IMG_EXTENSION

from .cached_data import CachedData
from .methods_handlers import BaseHandler, STFTHandler





class SignalEngine:
    def __init__(self, settings):
        self.settings = settings
        self.assign_ids(self.settings)
        
        self.lang = LanguageManager()
        self.cached_data = {}
        self.handled_files = {}
        
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
            
    def file_handle(self, source_program: str, file_path: str, channel: str):
        if source_program == MERA.id:
            'MERA file reader'
            reader = MeraReader(filepath=file_path)
            sampling_rate = reader.get_sampling_rate(channel)
            data = reader.read_channel(channel)
            return data, sampling_rate
        else:
            self.log_error(message=self.lang.get("logger.unknown_source_program", source_program=source_program))
            return None, None
        
    def read_and_cache(self, file_path: str, channel: str, source_program: str):
        key = CachedData.get_key(file_path=file_path, channel=channel)
         
        if key not in self.cached_data:
            data, sampling_rate = self.file_handle(source_program=source_program, file_path=file_path, channel=channel)

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
    
    def execute(self):
        errors = self.validate_settings_obj(self.settings)
        if len(errors) > 0:
            self.log_error(errors)
            return
        
        try:
            baseHandler = BaseHandler()
            files_settings = self.settings.get('files', [])
            for file_settings in files_settings:
                id = file_settings['id']
               
                settings = baseHandler.get_settings_by_id(settings=self.settings, target_id=id)
                if not settings:
                    return
                
                file_path = deep_get(settings, ["file_path"], '') 
                time_frames = deep_get(settings, ["time_frames"], []) 
                channels = deep_get(settings, ["channels"], []) 
                method = deep_get(settings, ["method"], '') 
                source_program = deep_get(settings, ["source_program"], '') 
                
                if not source_program:
                    self.log_error(message=self.lang.get("logger.field_required_error", field='source_program', file_settings=file_settings))
                    return
                
                # Checking mandatory parameters
                if not file_path:
                    self.log_error(message=self.lang.get("logger.field_required_error", field='file_path', file_settings=file_settings))
                    return
                
                
                
                self.handle_file(
                    source_program=source_program,
                    id=id,
                    file_path=file_path,
                    channels=channels,
                    time_frames=time_frames,
                    method=method
                )
                
        except Exception as e:
            self.log_error(message=str(e))
            
            
    def handle_file(
        self, 
        *,
        source_program,
        id,
        file_path,
        channels,
        time_frames,
        method    
    ):
        method_name = method['name']
        
        if method_name not in self.handled_files:
            self.handled_files[method_name] = {}
            
        for channel in channels:
            cached = self.read_and_cache(file_path=file_path, channel=channel, source_program=source_program)
            if cached is None:
                continue
            
            data = cached.data
            sampling_rate = cached.sampling_rate
            
            key = f"{id}___{channel}"
            if method_name == 'stft':
                handler = STFTHandler(
                    key=key, 
                    time_frames=time_frames,
                    method_settings=method,
                    channel=channel,
                    data=data,
                    sampling_rate=sampling_rate
                )
                handler.render_graphs(store_to=self.handled_files[method_name])
            else:
                self.log_error(message=self.lang.get("logger.method_not_implemented", method_name=method_name))
            
    
    def validate_settings_obj(self, settings):
        errors = []

        def log(msg):
            errors.append(msg)

        global_channels = settings.get('channels')
        global_source_program = settings.get('source_program')
        global_method = settings.get('method')

        if not isinstance(global_method, dict) or 'name' not in global_method:
            log(self.lang.get("logger.global_settings_error", method="method", name="name"))

        files = settings.get('files')
        if not isinstance(files, list):
            log(self.lang.get("logger.must_be_list", prop_name="files"))
            return errors

        # Check for 'groups_settings'
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
    
    def generate_settings_obj(self):
        return {}
    
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