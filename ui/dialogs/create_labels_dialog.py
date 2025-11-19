from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QMessageBox
)
from PyQt5.QtCore import Qt
import os
import json


class CreateLabelsDialog(QDialog):
    """Dialog to create label folder structure and initialize annotation files."""
    
    def __init__(self, image_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Label Files")
        self.setGeometry(100, 100, 500, 300)
        self.image_count = image_count
        self.selected_format = None
        self.create_files = False
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Create Label Files")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Info message
        info = QLabel(
            f"No label files found for {self.image_count} images.\n\n"
            "Select a format to initialize label files:"
        )
        layout.addWidget(info)
        
        # Format selection
        format_group = QButtonGroup()
        
        self.txt_radio = QRadioButton("TXT Format (.txt files)")
        self.json_radio = QRadioButton("JSON Format (.json files)")
        self.coco_radio = QRadioButton("COCO Format (_annotations.coco.json)")
        
        format_group.addButton(self.txt_radio, 0)
        format_group.addButton(self.json_radio, 1)
        format_group.addButton(self.coco_radio, 2)
        
        self.txt_radio.setChecked(True)
        
        layout.addWidget(self.txt_radio)
        layout.addWidget(self.json_radio)
        layout.addWidget(self.coco_radio)
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("Create Label Files")
        create_btn.setStyleSheet("background-color: #4a9eff; font-weight: bold; padding: 8px;")
        create_btn.clicked.connect(self._on_create)
        
        skip_btn = QPushButton("Skip")
        skip_btn.clicked.connect(self._on_skip)
        
        button_layout.addWidget(create_btn)
        button_layout.addWidget(skip_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _on_create(self):
        """Handle create button click."""
        if self.txt_radio.isChecked():
            self.selected_format = "TXT"
        elif self.json_radio.isChecked():
            self.selected_format = "JSON"
        elif self.coco_radio.isChecked():
            self.selected_format = "COCO"
        
        self.create_files = True
        self.accept()
    
    def _on_skip(self):
        """Handle skip button click."""
        self.create_files = False
        self.accept()
    
    def get_result(self):
        """Return (create_files: bool, selected_format: str or None)."""
        return self.create_files, self.selected_format


def create_label_structure(label_dir, image_count, format_type):
    """Create label folder structure and initialize files based on format.
    
    Args:
        label_dir: Path to labels directory
        image_count: Number of images
        format_type: 'TXT', 'JSON', or 'COCO'
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create label directory if it doesn't exist
        os.makedirs(label_dir, exist_ok=True)
        
        if format_type == "TXT":
            # For TXT format, just ensure the directory exists
            # Individual .txt files will be created as user annotates
            return True
        
        elif format_type == "JSON":
            # Create empty JSON files for each image (or just the directory structure)
            # The actual per-image JSON files will be created as user annotates
            return True
        
        elif format_type == "COCO":
            # Create the initial COCO format file
            coco_file = os.path.join(label_dir, "_annotations.coco.json")
            
            # Initialize COCO structure
            coco_data = {
                "info": {
                    "description": "Dataset for annotation",
                    "version": "1.0",
                    "year": 2024
                },
                "licenses": [],
                "images": [],
                "annotations": [],
                "categories": []
            }
            
            with open(coco_file, 'w') as f:
                json.dump(coco_data, f, indent=2)
            
            return True
        
        return False
    
    except Exception as e:
        return False
