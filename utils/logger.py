import os
import time
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from .constants import Constants

debug_log_flag = os.getenv(Constants.ENABLE_LOG_DEBUG, Constants.TRUE).lower() == Constants.TRUE
error_log_flag = os.getenv(Constants.ENABLE_LOG_ERROR, Constants.TRUE).lower() == Constants.TRUE
critical_log_flag = os.getenv(Constants.ENABLE_LOG_CRITICAL, Constants.TRUE).lower() == Constants.TRUE
info_log_level = os.getenv(Constants.ENABLE_LOG_INFO, Constants.TRUE).lower() == Constants.TRUE
warning_log_level = os.getenv(Constants.ENABLE_LOG_WARNING, Constants.TRUE).lower() == Constants.TRUE
retention_days = int(os.getenv(Constants.LOG_RETENTION_DAYS, str(Constants.ONE)))

# Timezone for logging
app_zone = ZoneInfo(Constants.TIME_ZONE_INFO)

class AppFormatter(logging.Formatter):
    def converter(self, timestamp):
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).astimezone(app_zone)

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()

class LoggingConfig:

    def __init__(self):
        self.logger = logging.getLogger()

    def setup_logging(self):
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        self.logger.setLevel(logging.DEBUG)

        log_directory = Constants.LOGGER_ROOT_FOLDER_NAME
        os.makedirs(log_directory, exist_ok=True)

        # Use fixed filenames for simplicity in this context
        debug_log_file = os.path.join(log_directory, 'debug.log')
        info_log_file = os.path.join(log_directory, 'info.log')

        debug_handler = TimedRotatingFileHandler(debug_log_file, when=Constants.MIDNIGHT, interval=Constants.ONE, backupCount=retention_days)
        info_handler = TimedRotatingFileHandler(info_log_file, when=Constants.MIDNIGHT, interval=Constants.ONE, backupCount=retention_days)
        console_handler = logging.StreamHandler(sys.stdout)

        debug_handler.setLevel(logging.DEBUG)
        info_handler.setLevel(logging.INFO)
        console_handler.setLevel(logging.INFO)

        time_format = '%Y-%m-%d %H:%M:%S'

        debug_formatter = AppFormatter('%(asctime)s - %(name)s.%(funcName)s - %(levelname)s <-> %(message)s', datefmt=time_format)
        info_formatter = AppFormatter('%(asctime)s - %(levelname)s <-> %(message)s', datefmt=time_format)

        debug_handler.setFormatter(debug_formatter)
        info_handler.setFormatter(info_formatter)
        console_handler.setFormatter(info_formatter)

        debug_handler.addFilter(self.DebugFilter())
        info_handler.addFilter(self.InfoFilter())
        console_handler.addFilter(self.InfoFilter())

        self.logger.addHandler(debug_handler)
        self.logger.addHandler(info_handler)
        self.logger.addHandler(console_handler)

        self.suppress_third_party_logs()
        logging.info("Logging configured successfully.")
        return self.logger

    def suppress_third_party_logs(self):
        noisy_loggers = ["PIL"]  # Add other noisy library names here
        for name in noisy_loggers:
            logging.getLogger(name).setLevel(logging.WARNING)

    class DebugFilter(logging.Filter):
        def filter(self, record):
            if debug_log_flag:
                return record.levelno in [logging.DEBUG, logging.ERROR, logging.CRITICAL]
            return record.levelno in [logging.ERROR, logging.CRITICAL]

    class InfoFilter(logging.Filter):
        def filter(self, record):
            if info_log_level:
                return record.levelno in [logging.INFO, logging.WARNING]
            elif warning_log_level:
                return record.levelno == logging.WARNING
            return False # If neither info nor warning is enabled, filter them out

def log_time(msg=None, info_log_level=False):
    """Decorator that logs the time taken by a function with a custom message."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            log_func = logging.info if info_log_level else logging.debug
            log_func(f"[{func.__name__}:-{msg or ''}] executed in {elapsed:.4f} seconds")
            return result
        return wrapper
    return decorator