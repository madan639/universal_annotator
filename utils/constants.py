"""Constants used throughout the application."""


class Constants:
    # --- Logging Configuration ---
    ENABLE_LOG_DEBUG = "ENABLE_LOG_DEBUG"
    ENABLE_LOG_ERROR = "ENABLE_LOG_ERROR"
    ENABLE_LOG_CRITICAL = "ENABLE_LOG_CRITICAL"
    ENABLE_LOG_INFO = "ENABLE_LOG_INFO"
    ENABLE_LOG_WARNING = "ENABLE_LOG_WARNING"
    LOG_RETENTION_DAYS = "LOG_RETENTION_DAYS"

    LOGGER_ROOT_FOLDER_NAME = "logs"
    TIME_ZONE_INFO = "UTC"  # Using UTC as a safe, universal default

    # --- String/Integer Constants ---
    TRUE = "true"
    MIDNIGHT = "midnight"
    ONE = 1