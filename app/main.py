from PyQt5.QtWidgets import QApplication
import sys
import os
import logging
from utils.logger import LoggingConfig
from core.app_window import AnnotatorMainWindow
from ui.themes import ThemeManager


def main():
    os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)

    # Force X11 backend (xcb) to avoid Wayland-specific warnings like 'requestActivate()'.
    os.environ['QT_QPA_PLATFORM'] = 'xcb'

    app = QApplication(sys.argv)
    
    # Setup logging
    log_config = LoggingConfig()
    log_config.setup_logging()
    
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
