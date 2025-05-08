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