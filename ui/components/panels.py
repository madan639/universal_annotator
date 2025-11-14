"""Panel components for organized layouts"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton, QLineEdit, QComboBox
from PyQt5.QtCore import Qt


class LabelPanel(QWidget):
    """Panel for displaying and managing annotation labels"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumWidth(280)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Annotations")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setMinimumHeight(34)
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.setMinimumHeight(34)
        
        buttons_layout.addWidget(self.select_all_btn)
        buttons_layout.addWidget(self.deselect_all_btn)
        layout.addLayout(buttons_layout)

        # Delete selected button
        self.delete_selected_btn = QPushButton("Delete Selected")
        self.delete_selected_btn.setMinimumHeight(34)
        layout.addWidget(self.delete_selected_btn)
        
        # Labels list
        self.labels_list = QListWidget()
        layout.addWidget(self.labels_list)
        
        self.setLayout(layout)


class ControlPanel(QWidget):
    """Main control panel with buttons and options"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # File operations
        file_label = QLabel("File Operations")
        file_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        layout.addWidget(file_label)
        
        self.load_btn = QPushButton("Load Dataset")
        self.load_btn.setMinimumHeight(36)
        layout.addWidget(self.load_btn)
        
        # Load classes file
        self.load_classes_btn = QPushButton("Select Classes File")
        self.load_classes_btn.setMinimumHeight(34)
        layout.addWidget(self.load_classes_btn)
        
        # Mode selection
        mode_label = QLabel("Mode")
        mode_label.setStyleSheet("font-weight: bold; font-size: 11px; margin-top: 10px;")
        layout.addWidget(mode_label)
        
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(8)
        
        self.mode_edit_btn = QPushButton("Edit Mode")
        self.mode_edit_btn.setMinimumHeight(34)
        self.mode_view_btn = QPushButton("View Mode")
        self.mode_view_btn.setMinimumHeight(34)
        
        mode_layout.addWidget(self.mode_edit_btn)
        mode_layout.addWidget(self.mode_view_btn)
        layout.addLayout(mode_layout)
        
        # Navigation
        nav_label = QLabel("Navigation")
        nav_label.setStyleSheet("font-weight: bold; font-size: 11px; margin-top: 10px;")
        layout.addWidget(nav_label)
        
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)
        
        self.prev_btn = QPushButton("Prev (A)")
        self.prev_btn.setMinimumHeight(34)
        self.next_btn = QPushButton("Next (D)")
        self.next_btn.setMinimumHeight(34)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        layout.addLayout(nav_layout)
        
        # Save and format buttons
        save_format_layout = QHBoxLayout()
        save_format_layout.setSpacing(8)
        
        self.save_btn = QPushButton("Save (S)")
        self.save_btn.setMinimumHeight(36)

        self.format_btn = QPushButton("Select Format")
        self.format_btn.setMinimumHeight(36)
        
        save_format_layout.addWidget(self.save_btn)
        save_format_layout.addWidget(self.format_btn)
        layout.addLayout(save_format_layout)
        
        # Image jump dropdown below the buttons
        self.image_jump_box = QComboBox()
        self.image_jump_box.setMinimumHeight(36)
        layout.addWidget(self.image_jump_box)
        
        # Current format display
        self.current_format_label = QLabel("Current Format: -")
        self.current_format_label.setStyleSheet("font-size: 10px; color: gray; margin-top: 2px;")
        self.current_format_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.current_format_label)
        
        # Format conversion
        conv_label = QLabel("Format Conversion")
        conv_label.setStyleSheet("font-weight: bold; font-size: 11px; margin-top: 10px;")
        layout.addWidget(conv_label)
        
        # Conversion buttons (line by line)
        self.convert_to_json_btn = QPushButton("Convert TXT to JSON")
        self.convert_to_json_btn.setMinimumHeight(34)
        layout.addWidget(self.convert_to_json_btn)

        self.convert_to_txt_btn = QPushButton("Convert JSON to TXT")
        self.convert_to_txt_btn.setMinimumHeight(34)
        layout.addWidget(self.convert_to_txt_btn)

        self.convert_to_coco_btn = QPushButton("Convert TXT to COCO")
        self.convert_to_coco_btn.setMinimumHeight(34)
        layout.addWidget(self.convert_to_coco_btn)

        self.merge_json_btn = QPushButton("Merge JSON to COCO")
        self.merge_json_btn.setMinimumHeight(34)
        layout.addWidget(self.merge_json_btn)

        self.convert_coco_to_json_btn = QPushButton("Convert COCO to JSONs")
        self.convert_coco_to_json_btn.setMinimumHeight(34)
        layout.addWidget(self.convert_coco_to_json_btn)

        self.convert_coco_to_txt_btn = QPushButton("Convert COCO to TXTs")
        self.convert_coco_to_txt_btn.setMinimumHeight(34)
        layout.addWidget(self.convert_coco_to_txt_btn)

        # Auto-save checkbox
        self.auto_save_cb = None  # Will be set by parent
        
        layout.addStretch()
        self.setLayout(layout)
