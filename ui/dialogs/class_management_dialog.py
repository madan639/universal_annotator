"""Custom dialog for managing class lists"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QDialogButtonBox
)
from PyQt5.QtGui import QFont


class ClassManagementDialog(QDialog):
    """A dialog to show current classes and allow manual entry of new ones."""

    def __init__(self, current_classes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Annotation Classes")
        self.setMinimumSize(450, 400)

        self.entered_classes = None

        # --- Layout ---
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # --- Display Current Classes ---
        title_font = QFont()
        title_font.setBold(True)

        current_label = QLabel("Currently Loaded Classes:")
        current_label.setFont(title_font)
        layout.addWidget(current_label)

        self.current_classes_display = QTextEdit()
        self.current_classes_display.setReadOnly(True)
        class_text = "\n".join(current_classes) if current_classes else "No classes loaded."
        self.current_classes_display.setText(class_text)
        self.current_classes_display.setMaximumHeight(100)
        layout.addWidget(self.current_classes_display)

        # --- Manual Entry Section ---
        manual_label = QLabel("Or, Enter New Classes Below (one per line):")
        manual_label.setFont(title_font)
        layout.addWidget(manual_label)

        self.manual_entry_edit = QTextEdit()
        self.manual_entry_edit.setPlaceholderText("person\ncar\nbicycle")
        layout.addWidget(self.manual_entry_edit)

        # --- OK and Cancel Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        """Override accept to process entered text."""
        text = self.manual_entry_edit.toPlainText()
        if text.strip():
            self.entered_classes = [line.strip() for line in text.split('\n') if line.strip()]
        super().accept()