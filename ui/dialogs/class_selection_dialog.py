"""Class selection dialog"""
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
from PyQt5.QtCore import Qt


class ClassSelectionDialog(QDialog):
    """Dialog to select class for a bbox"""
    def __init__(self, classes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Class for Bounding Box")
        self.setGeometry(100, 100, 450, 180)
        self.setModal(True)
        self.selected_class = 0
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        label = QLabel("Select the class for this bounding box:")
        label.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(label)
        
        # Class combo box
        self.class_combo = QComboBox()
        self.class_combo.addItems(classes)
        self.class_combo.setMinimumHeight(32)
        layout.addWidget(self.class_combo)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        ok_btn = QPushButton("OK")
        ok_btn.setMinimumHeight(32)
        ok_btn.setMinimumWidth(100)
        ok_btn.setObjectName("accentButton")
        ok_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(32)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(ok_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def get_selected_class(self):
        """Return the index of selected class"""
        return self.class_combo.currentIndex()
