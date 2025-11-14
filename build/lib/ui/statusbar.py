"""Custom Status Bar for Application"""
from PyQt5.QtWidgets import QStatusBar, QLabel, QWidget, QHBoxLayout, QSpacerItem
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSizePolicy


class AppStatusBar(QStatusBar):
    """Custom status bar with multiple sections"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create a container widget for the status bar
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(10)
        
        # Mode indicator
        self.mode_label = QLabel("VIEW MODE")
        self.mode_label.setMinimumWidth(100)
        layout.addWidget(self.mode_label)
        
        # Add separator
        separator = QLabel(" | ")
        layout.addWidget(separator)
        
        # Image info (position and count)
        self.image_info = QLabel("[0/0] No image loaded")
        self.image_info.setMinimumWidth(200)
        layout.addWidget(self.image_info)
        
        # Add separator
        separator2 = QLabel(" | ")
        layout.addWidget(separator2)
        
        # Box count
        self.box_count = QLabel("Boxes: 0")
        self.box_count.setMinimumWidth(80)
        layout.addWidget(self.box_count)
        
        # Add stretch (spacer)
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addSpacing(20)
        
        # Format indicator
        self.format_label = QLabel("Format: -")
        self.format_label.setMinimumWidth(120)
        layout.addWidget(self.format_label)
        
        # Status message
        self.status_message = QLabel("Ready")
        self.status_message.setMinimumWidth(150)
        layout.addWidget(self.status_message)
        
        container.setLayout(layout)
        self.addWidget(container, 1)
    
    def set_mode(self, mode):
        """Update mode indicator"""
        if mode == "edit":
            self.mode_label.setText("EDIT MODE")
            self.mode_label.setStyleSheet("color: #ff9800; font-weight: bold;")
        else:
            self.mode_label.setText("VIEW MODE")
            self.mode_label.setStyleSheet("color: #00bfff; font-weight: bold;")
    
    def set_image_info(self, current, total, filename=""):
        """Update image position and name"""
        if total > 0:
            self.image_info.setText(f"[{current}/{total}] {filename}")
        else:
            self.image_info.setText("[0/0] No image loaded")
    
    def set_box_count(self, count):
        """Update box count"""
        self.box_count.setText(f"Boxes: {count}")
    
    def set_format(self, format_name):
        """Update format indicator"""
        if format_name:
            self.format_label.setText(f"Format: {format_name}")
        else:
            self.format_label.setText("Format: -")
    
    def set_status(self, message, timeout=3000):
        """Show status message"""
        self.status_message.setText(message)
        if timeout > 0:
            self.showMessage(message, timeout)
