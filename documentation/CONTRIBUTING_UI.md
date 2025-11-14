# Contributing to Universal Annotator UI

## Getting Started

### Development Setup
1. Install PyQt5: `pip install PyQt5`
2. Install OpenCV: `pip install opencv-python`
3. Clone the repository
4. Run: `python main.py`

### Project Structure
```
universal_annotator/
├── core/              # Core application logic
├── ui/                # UI components and styling
├── exporters/         # Export format handlers
├── utils/             # Utility functions
└── main.py           # Application entry point
```

## UI Development Guidelines

### 1. Component Development

#### Creating Reusable Components
Place in `ui/components/`:

```python
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton

class MyComponent(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        # Add widgets here
        self.setLayout(layout)
```

#### Component Best Practices
- Keep components focused and single-purpose
- Accept customization parameters
- Emit signals for important events
- Include docstrings
- Use consistent naming conventions

### 2. Dialog Development

#### Creating Custom Dialogs
Place in `ui/dialogs/`:

```python
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton

class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("My Dialog")
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        # Add content
        self.setLayout(layout)
```

#### Dialog Best Practices
- Always set modal and window title
- Set appropriate geometry/size
- Include OK/Cancel buttons
- Return values via methods or signals
- Add proper styling

### 3. Theme Integration

#### Using Theme Colors
```python
from ui.themes import ThemeManager

theme = ThemeManager()
color = theme.get_color("primary")
stylesheet = theme.get_stylesheet()
```

#### Color Reference
- `primary`: Main background
- `secondary`: Secondary backgrounds
- `accent`: Highlighted elements
- `text_primary`: Main text color
- `text_secondary`: Secondary text
- `border`: Border color
- `success`: Success state color
- `warning`: Warning state color
- `danger`: Error state color

### 4. Tooltips and Messages

#### Adding Tooltips
Edit `ui/messages.py`:
```python
TOOLTIPS = {
    "my_button": "Click to perform action",
}

# In component:
button.setToolTip(get_tooltip("my_button"))
```

#### Adding Status Messages
```python
STATUS_MESSAGES = {
    "my_event": "Action completed successfully",
}

# Use in code:
self.app_status_bar.set_status(get_status_message("my_event"))
```

### 5. Styling Best Practices

#### Button Styling
```python
# Standard button
button = QPushButton("Click Me")
button.setMinimumHeight(32)

# Accent button
button = QPushButton("Important")
button.setObjectName("accentButton")

# Add tooltip
button.setToolTip("Helpful description")
```

#### Label Styling
```python
# Title
title = QLabel("Title")
title_font = QFont()
title_font.setBold(True)
title_font.setPointSize(14)
title.setFont(title_font)

# Subtitle
subtitle = QLabel("Subtitle")
subtitle.setStyleSheet("color: gray; font-size: 11px;")
```

#### Layout Margins and Spacing
```python
layout = QVBoxLayout()
layout.setContentsMargins(10, 10, 10, 10)  # L, T, R, B
layout.setSpacing(8)  # Space between items
```

### 6. Keyboard Shortcuts

#### Adding Menu Item with Shortcut
```python
action = file_menu.addAction("Save")
action.setShortcut("Ctrl+S")
action.triggered.connect(self.save_method)
```

#### Standard Shortcuts
Use `QKeySequence` for standard actions:
```python
action.setShortcut(QKeySequence.Open)    # Ctrl+O
action.setShortcut(QKeySequence.Save)    # Ctrl+S
action.setShortcut(QKeySequence.Quit)    # Ctrl+Q
action.setShortcut(QKeySequence.SelectAll)  # Ctrl+A
```

### 7. Testing Your Changes

#### Manual Testing
1. Test component in isolation
2. Test with dark and light themes
3. Test keyboard shortcuts
4. Verify tooltips and status messages
5. Test on different screen resolutions

#### Theme Testing
```python
# Test with dark theme
theme = ThemeManager("dark")
app.setStyleSheet(theme.get_stylesheet())

- Check for conflicts
- Test arrow key navigation
- Verify mouse and keyboard work together

## Code Style

### Python Style Guide
- Follow PEP 8
- Use meaningful variable names
- Add docstrings to functions and classes
- Use type hints where applicable

### Example
```python
def process_image(image_path: str, threshold: int = 127) -> bool:
    """
    Process an image with the given threshold.
    
    Args:
        image_path: Path to the image file
        threshold: Processing threshold value
    
    Returns:
        True if processing was successful, False otherwise
    """
    if not os.path.exists(image_path):
        return False
    
    # Process image
    return True
```

### Naming Conventions
- Classes: `PascalCase` (e.g., `MyComponent`)
- Functions/Methods: `snake_case` (e.g., `my_function()`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_SIZE`)
- Private: prefix with `_` (e.g., `_internal_method()`)

## Common Tasks

### Change Default Theme
Edit `main.py`:
```python
theme_manager = ThemeManager("light")  # Change to "light"
```

### Add New Menu Item
Edit `ui/menus.py`:
```python
def _create_tools_menu(self):
    """Create Tools menu"""
    tools_menu = self.addMenu("Tools")
    
    action = tools_menu.addAction("My Tool")
    action.setShortcut("Ctrl+T")
    action.triggered.connect(self.parent.my_tool_method)
```

### Create New Color Pair
Edit `ui/themes/theme_manager.py`:
```python
DARK_THEME = {
    # ... existing colors ...
    "my_color": "#ff0000",
}

LIGHT_THEME = {
    # ... existing colors ...
    "my_color": "#0000ff",
}
```

### Add New Status Message Type
Edit `ui/messages.py`:
```python
STATUS_MESSAGES = {
    # ... existing messages ...
    "my_action": "My action completed",
}
```

## Debugging

### Enable Debug Logging
Add to your component:
```python
import logging

logger = logging.getLogger(__name__)
logger.debug(f"Component initialized: {self}")
```

### Check Theme Application
```python
# Verify stylesheet is applied
print(app.styleSheet()[:100])  # Print first 100 chars

# Check specific widget
print(widget.styleSheet())
```

### Inspect Layout Issues
```python
# Print layout structure
def print_layout(widget, indent=0):
    layout = widget.layout()
    print("  " * indent + f"{widget.__class__.__name__}")
    if layout:
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget():
                print_layout(item.widget(), indent + 1)
```

## Pull Request Guidelines

### Before Submitting
1. [ ] Code follows PEP 8 style guide
2. [ ] Added/updated docstrings
3. [ ] Tested with the dark theme
4. [ ] Verified keyboard shortcuts work
5. [ ] Updated documentation if needed
6. [ ] No debug print statements left
7. [ ] No unused imports

### PR Description
Include:
- What was changed and why
- How to test the changes
- Any new dependencies
- Screenshots if UI changes
- Related issues/features

### Example PR Title
- `feat: Add dark/light theme toggle`
- `fix: Resolve menu bar styling issue`
- `refactor: Extract button components`
- `docs: Update UI guide`

## Resources

### PyQt5 Documentation
- [Official PyQt5 Docs](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [QWidget Documentation](https://doc.qt.io/qt-5/qwidget.html)
- [QMainWindow Documentation](https://doc.qt.io/qt-5/qmainwindow.html)

### Design Resources
- [PyQt5 Styling](https://doc.qt.io/qt-5/stylesheet-reference.html)
- [UI/UX Best Practices](https://www.nngroup.com/articles/)
- [Material Design Guidelines](https://material.io/design)

### Useful Tools
- `QDesigner`: Visual UI builder (optional)
- `Qt Documentation`: Built-in help
- `PyCharm`: IDE with Qt support

## Getting Help

- Check existing issues and discussions
- Read the UI_IMPROVEMENTS.md documentation
- Ask in pull request comments
- Create detailed issue reports with screenshots

## Community

- Report bugs with minimal reproducible example
- Suggest features with clear use cases
- Help review pull requests
- Improve documentation

Thank you for contributing to Universal Annotator! 🎉
