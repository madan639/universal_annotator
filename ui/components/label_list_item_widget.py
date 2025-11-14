"""Custom widget for items in the labels list"""
import logging
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel, QPushButton, QSizePolicy, QStyle
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QMouseEvent


class ClickableLabel(QLabel):
    """A QLabel that emits a signal when clicked."""
    clicked = pyqtSignal(QMouseEvent)

    def mousePressEvent(self, event: QMouseEvent):
        self.clicked.emit(event)
        super().mousePressEvent(event)


class LabelListItemWidget(QWidget):
    """
    Custom widget for each item in the labels list, containing a checkbox,
    a clickable label, and a delete button.
    """
    delete_requested = pyqtSignal(int)  # Emits box_idx
    selection_toggled = pyqtSignal(int, bool)  # Emits box_idx, is_checked
    label_clicked = pyqtSignal(int, QMouseEvent)  # Emits box_idx, mouse_event

    def __init__(self, box_idx, class_name, is_checked, parent=None):
        super().__init__(parent)
        self.box_idx = box_idx

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(is_checked)
        
        def _on_state_changed(state):
            checked = (state == Qt.Checked)
            self.selection_toggled.emit(self.box_idx, checked)

        self.checkbox.stateChanged.connect(_on_state_changed)
        layout.addWidget(self.checkbox)

        # Label
        self.label = ClickableLabel(f"{self.box_idx}: {class_name}")
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.label.clicked.connect(lambda event: self.label_clicked.emit(self.box_idx, event))
        layout.addWidget(self.label)

        # Delete button
        self.delete_button = QPushButton()
        self.delete_button.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.delete_button.setFixedSize(30, 30)
        self.delete_button.setIconSize(QSize(16, 16))
        self.delete_button.setToolTip("Delete this box")
        self.delete_button.clicked.connect(lambda: self.delete_requested.emit(self.box_idx))
        layout.addWidget(self.delete_button)

        self.setLayout(layout)