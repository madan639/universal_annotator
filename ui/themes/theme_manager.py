"""Theme Manager for Dark/Light mode styling"""

# Color palettes
DARK_THEME = {
    "primary": "#1e1e2e",      # Dark background
    "secondary": "#2d2d44",    # Slightly lighter background
    "accent": "#00bfff",       # Bright cyan
    "success": "#00ff00",      # Green
    "warning": "#ff9800",      # Orange
    "danger": "#ff4444",       # Red
    "text_primary": "#ffffff", # White text
    "text_secondary": "#b0b0b0", # Gray text
    "border": "#404040",       # Dark border
    "button_hover": "#3d3d5c",
    "highlight": "#ff9800",    # Orange highlight
}


class ThemeManager:
    """Manages application themes and stylesheets"""
    
    def __init__(self):
        self.current_theme = DARK_THEME

    def get_stylesheet(self):
        """Generate complete stylesheet based on current theme"""
        theme = self.current_theme
        
        stylesheet = f"""
        QMainWindow {{
            background-color: {theme['primary']};
            color: {theme['text_primary']};
        }}
        
        QWidget {{
            background-color: {theme['primary']};
            color: {theme['text_primary']};
        }}
        
        QLabel {{
            color: {theme['text_primary']};
            font-size: 12px;
        }}
        
        QPushButton {{
            background-color: {theme['secondary']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 4px;
            padding: 8px 14px;
            font-weight: bold;
            font-size: 12px;
        }}
        
        QPushButton:hover {{
            background-color: {theme['button_hover']};
            border: 1px solid {theme['accent']};
        }}
        
        QPushButton:pressed {{
            background-color: {theme['accent']};
            color: white;
        }}
        
        QPushButton#accentButton {{
            background-color: {theme['accent']};
            color: white;
        }}
        
        QPushButton#accentButton:hover {{
            opacity: 0.9;
        }}
        
        QCheckBox {{
            color: {theme['text_primary']};
            spacing: 5px;
            font-size: 12px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
        }}
        
        QCheckBox::indicator:unchecked {{
            background-color: {theme['secondary']};
            border: 1px solid {theme['border']};
            border-radius: 3px;
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {theme['accent']};
            border: 1px solid {theme['accent']};
            border-radius: 3px;
        }}
        
        QComboBox {{
            background-color: {theme['secondary']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 4px;
            padding: 6px;
            font-size: 12px;
        }}
        
        QComboBox::drop-down {{
            border: none;
            background-color: transparent;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {theme['secondary']};
            color: {theme['text_primary']};
            selection-background-color: {theme['accent']};
            border: 1px solid {theme['border']};
        }}
        
        QListWidget {{
            background-color: {theme['secondary']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 4px;
        }}
        
        QListWidget::item {{
            padding: 4px;
        }}
        
        QListWidget::item:selected {{
            background-color: {theme['accent']};
            color: white;
        }}
        
        QListWidget::item:hover {{
            background-color: {theme['button_hover']};
        }}
        
        QDialog {{
            background-color: {theme['primary']};
            color: {theme['text_primary']};
        }}
        
        QMessageBox {{
            background-color: {theme['primary']};
        }}
        
        QMessageBox QLabel {{
            color: {theme['text_primary']};
        }}
        
        QGroupBox {{
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
            font-size: 12px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }}
        
        QTabWidget {{
            background-color: {theme['primary']};
        }}
        
        QTabBar::tab {{
            background-color: {theme['secondary']};
            color: {theme['text_primary']};
            padding: 8px 22px;
            border: 1px solid {theme['border']};
            border-bottom: none;
            border-radius: 4px 4px 0 0;
            font-size: 12px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {theme['accent']};
            color: white;
        }}
        
        QStatusBar {{
            background-color: {theme['secondary']};
            color: {theme['text_primary']};
            border-top: 1px solid {theme['border']};
        }}
        
        QScrollBar:vertical {{
            background-color: {theme['primary']};
            width: 12px;
            margin: 0px 0px 0px 0px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {theme['secondary']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {theme['accent']};
        }}
        
        QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}
        
        QScrollBar::add-line:vertical {{
            border: none;
            background: none;
        }}
        
        QScrollBar:horizontal {{
            background-color: {theme['primary']};
            height: 12px;
            margin: 0px 0px 0px 0px;
            border: none;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {theme['secondary']};
            border-radius: 6px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {theme['accent']};
        }}
        
        QScrollBar::sub-line:horizontal {{
            border: none;
            background: none;
        }}
        
        QScrollBar::add-line:horizontal {{
            border: none;
            background: none;
        }}
        """
        
        return stylesheet

    def get_color(self, color_name):
        """Get a specific color from the current theme"""
        return self.current_theme.get(color_name, "#ffffff")
