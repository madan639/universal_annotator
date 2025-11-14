# Universal Annotator - UI Improvements Guide

## Overview

The Universal Annotator now features a professional, modern UI with comprehensive help, keyboard shortcuts, and status bar information. The UI has been refactored into modular components for better maintainability and extensibility.

## New Features

### 1. **Modern Theme System** 🎨
- A professional dark theme is used by default.
- Customizable theme support through `ThemeManager`
# 2. **Menu Bar** 📋
- **File Menu**: Load Dataset, Select Format, Save, Exit
- **Edit Menu**: Edit/View Mode, Delete Box, Select/Deselect All
- **View Menu**: Navigation, Refresh Image, Toggle Auto-Save
- **Help Menu**: Help Dialog, About Dialog

### 3. **Comprehensive Status Bar** 📊
- Current mode indicator (Edit/View)
- Image position and filename
- Box count display
- Selected annotation format
- Real-time status messages

### 4. **Help System** ❓
- **Getting Started**: Basic workflow and supported formats
- **Keyboard Shortcuts**: Complete shortcut reference
- **Tips & Tricks**: Best practices and troubleshooting

### 5. **Keyboard Shortcuts** ⌨️
#### Navigation
- `A` - Previous Image
- `D` - Next Image
- `←` / `→` - Navigate between images

#### Editing
- `E` - Toggle Edit Mode
- `V` - Toggle View Mode
- `Delete` - Remove last bounding box
- `S` - Save current image

#### Selection
- `Ctrl+A` - Select All Boxes
- `Ctrl+D` - Deselect All Boxes

#### General
- `Esc` / `Q` - Exit Application
- `F1` - Open Help Dialog
- `F5` - Refresh Current Image

### 6. **Tooltips** 💡
All buttons and controls have helpful tooltips that explain their function.

### 7. **Status Messages** 📝
Real-time feedback for user actions:
- Dataset loaded successfully
- Annotation format selected
- Image saved
- Bounding boxes added/removed
- Mode changes
- Selection changes

## Project Structure

```
ui/
├── __init__.py              # UI module exports
├── menus.py                 # Menu bar creation
├── messages.py              # Tooltips and status messages
├── statusbar.py             # Custom status bar
├── themes/ 
│   ├── __init__.py
│   └── theme_manager.py     # Theme system with dark/light modes
├── components/ 
│   ├── __init__.py
│   ├── buttons.py           # Reusable button components
│   └── panels.py            # Control and label panels
└── dialogs/
    ├── __init__.py
    ├── class_selection_dialog.py  # Class selection dialog
    └── help_about_dialog.py       # Help and about dialogs
```

## Usage

### Apply Theme to Application
```python
from ui.themes import ThemeManager

theme = ThemeManager()
```

### Create Help Dialog
```python
from ui.dialogs import HelpDialog

help_dialog = HelpDialog(parent=self)
help_dialog.exec_()
```

### Get Tooltips and Status Messages
```python
from ui.messages import get_tooltip, get_status_message

tooltip = get_tooltip("load_dataset")
status = get_status_message("dataset_loaded")
```

### Update Status Bar
```python
self.app_status_bar.set_image_info(1, 10, "image.jpg")
self.app_status_bar.set_box_count(5)
self.app_status_bar.set_format("TXT")
self.app_status_bar.set_status("Operation completed")
```

## Best Practices

### For Developers
1. **Add tooltips** to new UI elements using `get_tooltip()`
2. **Use status messages** for user feedback via `set_status()`
3. **Keep the theme consistent** - modify colors in `theme_manager.py`
4. **Use reusable components** from `components/` folder
5. **Create dialogs** in `dialogs/` folder with proper styling

### For Users
1. **Learn keyboard shortcuts** - they significantly speed up workflow
2. **Enable auto-save** to prevent data loss
3. **Check status bar** for real-time feedback
4. **Use Help (F1)** for guidance and troubleshooting
5. **Review tips** for annotation best practices

## Customization

### Adding a New Tooltip
Edit `ui/messages.py`:
```python
TOOLTIPS = {
    "your_button": "Your helpful tooltip text",
}
```

### Adding a New Status Message
Edit `ui/messages.py`:
```python
STATUS_MESSAGES = {
    "your_event": "Status message here",
}
```

### Creating a Custom Dialog
1. Create file in `ui/dialogs/`
2. Inherit from `QDialog`
3. Apply theme colors using `ThemeManager`
4. Update `ui/dialogs/__init__.py` exports

### Modifying Theme Colors
Edit `ui/themes/theme_manager.py`:
```python
DARK_THEME = {
    "primary": "#1e1e2e",
    "accent": "#00bfff",
    # ... more colors
}
```

## Keyboard Shortcuts by Category

### Quick Reference
| Category | Shortcut | Action |
|----------|----------|--------|
| Navigation | A | Previous |
| Navigation | D | Next |
| Editing | E | Edit Mode |
| Editing | V | View Mode |
| Editing | Del | Delete Box |
| Editing | S | Save |
| Selection | Ctrl+A | Select All |
| Selection | Ctrl+D | Deselect All |
| Help | F1 | Help Dialog |
| Exit | Esc | Close App |

## Help Dialog Features

### Getting Started Tab
- Basic workflow explanation
- Supported annotation formats
- Mode descriptions

### Keyboard Shortcuts Tab
- All available shortcuts
- Organized by category
- Easy reference table

### Tips & Tricks Tab
- Efficient annotation techniques
- Best practices
- Troubleshooting guide
- Common issues and solutions

## Status Bar Information

The status bar provides real-time information:

```
[Position/Total] Filename | Boxes: Count | Format: Type
```

Example: `[5/20] image_005.jpg | Boxes: 3 | Format: TXT`

## Troubleshooting

### UI Elements Not Styled
- Ensure theme is applied: `app.setStyleSheet(theme.get_stylesheet())`
- Check element object names match stylesheet

### Tooltips Not Showing
- Call `_setup_tooltips()` in initialization
- Ensure tooltips are enabled in application settings

### Status Bar Messages Not Appearing
- Verify `app_status_bar` is initialized
- Check message key exists in `STATUS_MESSAGES`

### Help Dialog Won't Open
- Verify imports: `from ui.dialogs import HelpDialog`
- Check parent window is passed correctly

## Future Enhancements

Potential improvements:
- Custom keyboard shortcuts dialog
- Theme presets (Nord, Dracula, Solarized)
- Annotation statistics dashboard
- Undo/Redo functionality
- Batch annotation tools
- Plugin system for custom tools

## Contributing

When contributing UI improvements:
1. Keep components modular and reusable
2. Add appropriate tooltips and status messages
3. Follow the existing color scheme
4. Update this documentation
5. Test UI changes thoroughly
