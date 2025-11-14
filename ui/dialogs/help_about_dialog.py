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
        text.setMarkdown("""
# Getting Started with Universal Annotator

## Basic Workflow

1. **Load Dataset**: Click "Load Dataset" to select your image and label folders.
2. **Select Format**: The format is auto-detected, or you can select it manually.
3. **Switch to Edit Mode**: Press **E** to start annotating.
4. **Enter Drawing Mode**: Press **M** to enable drawing, then click and drag on the image to create boxes.
5. **Select Class**: Choose the class when prompted
6. **Navigate**: Use Previous/Next buttons or A/D keys to move between images
7. **Save**: Click "Save (S)" or use auto-save

## Supported Formats

- **TXT**: .txt files with normalized coordinates
- **JSON**: Custom JSON format with absolute coordinates
- **COCO**: COCO-format JSON with multiple images per file

## Modes

- **View Mode**: Read-only mode for reviewing annotations
- **Edit Mode**: Add, modify, and manage annotations

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
| `←` `→` | Navigate between images |

## Editing
| Key | Action |
|-----|--------|
| `E` | Toggle Edit Mode |
| `V` | Toggle View Mode |
| `M` | Enter/Exit Drawing Mode (in Edit Mode) |
| `X` | Exit Drawing Mode (returns to selection) |
| `Delete` | Remove selected bounding box(es) |
| `S` | Save current image |
| `Esc` | Cancel drawing a new box (while dragging) |

## Selection
| Key | Action |
|-----|--------|
| `Ctrl+A` | Select All Boxes |
| `Ctrl+D` | Deselect All Boxes |

## General
| Key | Action |
|-----|--------|
| `Esc` / `Q` | Exit Application |
| `F1` | Open Help Dialog |
| `F5` | Refresh Current Image |

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
        text.setMarkdown("""
# Tips & Tricks

## Efficient Annotation
1. **Use Keyboard Shortcuts**: `A` and `D` for navigation, `E` for Edit Mode, and `M` for Drawing Mode are essential for speed.
2. **Jump to Image**: Use the dropdown list below the "Save" button to jump directly to any image in your dataset.
3. **Auto-Save**: Enable auto-save to avoid losing work when navigating between images.
4. **Quick Deletion**: Use the trash bin icon next to any annotation in the right-hand panel to delete it instantly.
5. **Cancel Drawing**: If you make a mistake while drawing a box, press `Esc` before releasing the mouse to cancel it.
6. **Smart Selection**: When boxes overlap, clicking on them automatically selects the smallest box under your cursor. This makes it easy to select and delete inner boxes.
7. **Single Selection**: To quickly select just one box, click it directly on the image. All other boxes will be deselected.

## Best Practices

### Annotation Quality
- Draw boxes tightly around objects
- Include full object within the box
- Be consistent with box placement
- Use appropriate class labels

### Dataset Organization
- Keep images and labels in separate folders
- Use consistent file naming (6f.jpg with 6f.txt)
- Ensure images are readable formats (JPG, PNG)
- Verify labels before exporting

### Performance
- Use smaller images for faster interaction
- Disable unnecessary overlays in view mode
- Clear unused selections to reduce clutter
- Use the format conversion buttons to easily switch between annotation types.
- Save regularly to avoid data loss

## Troubleshooting

### Images not loading
- Check image folder path
- Ensure files are supported formats (JPG, PNG, BMP)
- Verify file permissions

### Labels not appearing
- Ensure labels folder is selected correctly
- Check annotation format matches files
- Verify label file naming matches images

### Box drawing issues
- Make sure you are in **Edit Mode** (press `E`).
- Make sure you are in **Drawing Mode** (press `M`). The status bar will confirm this.
- Click and drag to create boxes. They must be larger than 5x5 pixels.

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
