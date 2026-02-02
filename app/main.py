from PyQt5.QtWidgets import QApplication
import sys
import os
import logging
from utils.logger import LoggingConfig
from core.app_window import AnnotatorMainWindow
from ui.themes import ThemeManager
import platform

def configure_qt_platform():
    system = platform.system().lower()
    logging.debug(f"Configuring Qt platform for {system}.")

    os.environ.pop("QT_QPA_PLATFORM", None)
    os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)

    if system == "linux":
        os.environ["QT_QPA_PLATFORM"] = "xcb"
    elif system == "windows":
        os.environ["QT_QPA_PLATFORM"] = "windows"

    
def main():
        # Setup logging ONCE
    log_config = LoggingConfig()
    log_config.setup_logging()

    configure_qt_platform()

    app = QApplication(sys.argv)
    
    
    # Apply dark theme to entire application
    theme_manager = ThemeManager()
    app.setStyle("Fusion")
    app.setStyleSheet(theme_manager.get_stylesheet())
    
    window = AnnotatorMainWindow()
    window.show()
    
    try:
        exit_code = app.exec_()
        logging.info(f"Application exiting with code {exit_code}.")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logging.warning("Application cancelled by user from terminal (Ctrl+C).")
        sys.exit(1)


