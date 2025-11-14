"""Styled button components"""
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt


class StyledButton(QPushButton):
    """Standard styled button"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(32)
        self.setCursor(Qt.PointingHandCursor)


class ActionButton(QPushButton):
    """Action button with accent color"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(32)
        self.setObjectName("accentButton")
        self.setCursor(Qt.PointingHandCursor)
