from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QRadioButton, QButtonGroup, QLabel, QWidget
from PyQt5.QtCore import pyqtSignal
from universal_annotator.core.enums import AppMode, DrawingTool
class ModePanel(QGroupBox):
    """
    Panel to select Application Mode (Detection/Segmentation) and Drawing Tool.
    """
    mode_changed = pyqtSignal(object)  # Emits AppMode enum
    tool_changed = pyqtSignal(object)  # Emits DrawingTool enum
    def __init__(self, parent=None):
        super().__init__("Annotation Mode", parent)
        self.setMinimumHeight(200) # Force visible height
        self.setStyleSheet("QGroupBox { border: 1px solid gray; margin-top: 10px; font-weight: bold; }")
        self.layout = QVBoxLayout(self)
        
        # --- Task Mode Section ---
        self.mode_group = QButtonGroup(self)
        
        self.rb_detection = QRadioButton("Annotation")
        self.rb_detection.setChecked(True) # Default
        self.mode_group.addButton(self.rb_detection)
        self.layout.addWidget(self.rb_detection)
        
        self.rb_segmentation = QRadioButton("Segmentation")
        self.mode_group.addButton(self.rb_segmentation)
        self.layout.addWidget(self.rb_segmentation)
        
        self.mode_group.buttonClicked.connect(self._on_mode_changed)
        # --- Separator/Label ---
        self.layout.addSpacing(10)
        self.tool_label = QLabel("Drawing Tool:")
        self.layout.addWidget(self.tool_label)
        # --- Tool Section ---
        self.tool_group = QButtonGroup(self)
        
        self.rb_rect = QRadioButton("Rectangle (BBox)")
        self.rb_rect.setChecked(True)
        self.tool_group.addButton(self.rb_rect)
        self.layout.addWidget(self.rb_rect)
        
        self.rb_poly = QRadioButton("Polygon")
        self.tool_group.addButton(self.rb_poly)
        self.layout.addWidget(self.rb_poly)
        
        self.tool_group.buttonClicked.connect(self._on_tool_changed)
        
        self.layout.addStretch()
    def _on_mode_changed(self, button):
        if button == self.rb_detection:
            self.mode_changed.emit(AppMode.DETECTION)
            # Detection supports both tools? Usually yes.
            self.rb_rect.setEnabled(True)
            self.rb_poly.setEnabled(True)
        else:
            self.mode_changed.emit(AppMode.SEGMENTATION)
            # Segmentation typically implies Polygons only (for now)
            # Or maybe user wants BBox for weak segmentation?
            # Let's enforce Polygon for Segmentation as per typical workflow
            self.rb_poly.setChecked(True)
            self.tool_changed.emit(DrawingTool.POLYGON) 
            self.rb_rect.setEnabled(False) # Disable rectangle if strict segmentation
    def _on_tool_changed(self, button):
        if button == self.rb_rect:
            self.tool_changed.emit(DrawingTool.RECTANGLE)
        else:
            self.tool_changed.emit(DrawingTool.POLYGON)
