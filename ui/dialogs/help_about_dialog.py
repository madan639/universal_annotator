"""Help and About Dialogs"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QTabWidget, QWidget, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap


class HelpDialog(QDialog):
    """Comprehensive help dialog with keyboard shortcuts"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help & Keyboard Shortcuts")
        self.setGeometry(100, 100, 700, 600)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Universal Annotator - Help Guide")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Tabs
        tabs = QTabWidget()
        
        # Getting Started Tab
        getting_started = self._create_getting_started_tab()
        tabs.addTab(getting_started, "Getting Started")
        
        # Keyboard Shortcuts Tab
        shortcuts = self._create_shortcuts_tab()
        tabs.addTab(shortcuts, "Keyboard Shortcuts")
        
        # Format Conversion Tab
        conversion = self._create_conversion_tab()
        tabs.addTab(conversion, "Format Conversion")
        
        # Tips Tab
        tips = self._create_tips_tab()
        tabs.addTab(tips, "Tips & Tricks")
        
        layout.addWidget(tabs)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(36)
        close_btn.setObjectName("accentButton")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def _create_getting_started_tab(self):
        """Create Getting Started tab content"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setMarkdown("""# Getting Started with Universal Annotator

## Basic Workflow

1. **Load Dataset**: Click "Load Dataset" to select your image and label folders.
2. **Select Format**: The format is auto-detected, or you can select it manually.
3. **Edit existing boxes**: Press **E** — you can now click-drag boxes to move them, or drag handles to resize.
4. **Draw new boxes**: Press **M** — click and drag on the image to create a new box.
5. **Navigate**: Use `A` / `D` keys or Previous/Next buttons to move between images.
6. **Save**: Press `S` or click "Save".
7. **View Mode**: Press `X` to enter read-only view.

## Supported Formats

- **TXT**: .txt files with normalized coordinates
- **JSON**: Custom JSON format with absolute coordinates
- **COCO**: COCO-format JSON with multiple images per file

## Modes

| Mode | Key | Colour | Description |
|------|-----|--------|-------------|
| Edit | `E` | 🟠 Orange | Move / resize existing boxes |
| Draw | `M` | 🟢 Green | Draw a brand-new box |
| View | `X` | 🔵 Blue | Read-only, no changes |

        """)
        layout.addWidget(text)
        widget.setLayout(layout)
        return widget
    
    def _create_shortcuts_tab(self):
        """Create Keyboard Shortcuts tab content"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setMarkdown("""
# Keyboard Shortcuts

## Navigation
| Key | Action |
|-----|--------|
| `A` | Previous Image |
| `D` | Next Image |

## Mode Switching
| Key | Colour | Action |
|-----|--------|--------|
| `E` | 🟠 Orange | **Edit mode** — move & resize existing boxes/polygons |
| `M` | 🟢 Green | **Draw mode** — click and drag to create a new box |
| `X` | 🔵 Blue | **View mode** — read-only, no changes |
| `Esc` | — | Cancel drawing / go to View mode |

## Editing
| Key | Action |
|-----|--------|
| `Delete` | Delete selected box(es) or polygon(s) |
| `S` | Save current annotations |
| `C` | Cancel in-progress polygon or box draw |
| `Enter` | Close polygon (Segmentation mode) |
| Double-click box | Change the class of that annotation |

## Selection
| Key | Action |
|-----|--------|
| `Ctrl+A` | Select All |
| `Ctrl+D` | Deselect All |

## General
| Key | Action |
|-----|--------|
| `Q` | Quit application |
| `F1` | Open Help |

        """)
        layout.addWidget(text)
        widget.setLayout(layout)
        return widget
    
    def _create_conversion_tab(self):
        """Create Format Conversion tab content"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setMarkdown("""
# Format Conversion

The tool provides several utilities to convert between annotation formats:

- **Convert TXT to JSON**: Converts a folder of TXT files to individual JSON files.
- **Convert JSON to TXT**: Converts a folder of JSON files to TXT files.
- **Convert TXT to COCO**: Converts a folder of TXT files into a single `_annotations.coco.json` file.
- **Merge JSON to COCO**: Merges a folder of individual JSON files into a single `_annotations.coco.json` file.
- **Convert COCO to JSONs**: Splits a COCO file into multiple per-image JSON files.
- **Convert COCO to TXTs**: Splits a COCO file into multiple `.txt` files.

        """)
        layout.addWidget(text)
        widget.setLayout(layout)
        return widget
    
    def _create_tips_tab(self):
        """Create Tips & Tricks tab content"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setMarkdown("""# Tips & Tricks

## Working with Annotations
1. **Press E first** to enter Edit mode, then drag any box to move it or grab a blue handle to resize.
2. **Press M** when you want to draw a brand-new box; press E again when done.
3. **Double-click** any box or polygon (canvas or side list) to change its class instantly.
4. **Jump to Image**: Use the dropdown below the Save button to jump directly to any image.
5. **Quick Deletion**: Use the trash icon next to any annotation in the right-hand panel, or select and press Delete.
6. **Smart Selection**: When boxes overlap, the smallest box under your cursor is selected.
7. **Polygon Vertex Drag**: In Edit mode, click near a polygon vertex dot and drag to reshape it.

## Best Practices

### Annotation Quality
- Draw boxes tightly around objects
- Include the full object within the box
- Be consistent with class labels

### Dataset Organization
- Keep images and labels in separate folders
- Use consistent file naming
- Save regularly to avoid data loss

## Troubleshooting

### Box drawing not working
- Make sure you are in **Draw Mode** (press `M`). The status bar turns green.

### Can't move or resize boxes
- Make sure you are in **Edit Mode** (press `E`). Blue handles appear on selected boxes.

### Polygon Drawing (Segmentation Mode)
- **Left Click**: Add points.
- **Right Click** or **Enter**: Finish the polygon.
- **Esc**: Cancel the current drawing.

        """)
        layout.addWidget(text)
        widget.setLayout(layout)
        return widget


class AboutDialog(QDialog):
    """About dialog with version and credits"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Universal Annotator")
        self.setGeometry(100, 100, 500, 400)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Universal Annotator")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Version
        version = QLabel("Version 1.0.0")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(version)
        
        # Description
        description = QLabel(
            "A comprehensive tool for annotating images with bounding boxes.\n"
            "Supports multiple annotation formats including TXT, JSON, and COCO."
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Features
        features = QLabel(
            "<b>Features:</b><br>"
            "• Multiple annotation formats<br>"
            "• Keyboard shortcuts for efficiency<br>"
            "• Auto-save functionality<br>"
            "• Natural image sorting<br>"
            "• Selection memory per image<br>"
            "• Dark/Light theme support"
        )
        features.setAlignment(Qt.AlignCenter)
        features.setWordWrap(True)
        layout.addWidget(features)
        
        # Credits
        credits = QLabel(
            "<b>Built with:</b><br>"
            "PyQt5 • OpenCV • NumPy"
        )
        credits.setAlignment(Qt.AlignCenter)
        credits.setWordWrap(True)
        layout.addWidget(credits)
        
        layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(36)
        close_btn.setObjectName("accentButton")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
