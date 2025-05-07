import logging
import sys
import os
from pathlib import Path

def setup_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    is_frozen = getattr(sys, 'frozen', False)

    if is_frozen:
        # Path to "My Documents"
        documents_path = Path.home() / "Documents"
        logs_dir = documents_path / "AppLogs"
        logs_dir.mkdir(exist_ok=True)

        log_file = logs_dir / "app.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Log also to console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    else:
        # Only console (when running as a script)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

Logger = setup_logger()