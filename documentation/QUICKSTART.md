# Quick Start Guide

## Getting Started in 5 Minutes

### Step 1: Installation
```bash
# Clone or navigate to project
cd universal_annotator

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Step 2: Prepare Your Data
1. Create two folders:
   - `my_images/` - containing your images (JPG, PNG, etc.)
   - `my_labels/` - for storing annotations (can be empty)

2. Edit `classes.txt` with your classes:
```
cat
dog
bird
```

### Step 3: Load Dataset
1. Click **"Load Dataset"** button
2. Select your `my_images/` folder
3. Select your `my_labels/` folder
4. Choose annotation format (TXT recommended for beginners)

### Step 4: Start Annotating
1. Click **"Edit Mode"** button
2. Click and drag on image to draw boxes
3. Select class when prompted
4. Use **A** and **D** keys to navigate between images
5. Press **S** to save

### Step 5: Export
Your annotations are automatically saved in the selected format:
- **TXT**: `.txt` files with normalized coordinates
- **JSON**: Custom JSON format
- **COCO**: Single JSON file with all annotations

## Keyboard Shortcuts (Essential)

| Key | Action |
|-----|--------|
| **A** | Previous image |
| **D** | Next image |
| **E** | Edit mode |
| **V** | View mode |
| **Delete** | Remove last box |
| **S** | Save |
| **F1** | Help |
| **Esc** | Exit |

## Common Tasks

### Switch Between Edit and View Mode
- **Edit Mode**: Draw and modify boxes
  - Click "Edit Mode" or press **E**
  
- **View Mode**: Review annotations only
  - Click "View Mode" or press **V**

### Navigate Images
- **Next Image**: Press **D** or click "Next" button
- **Previous Image**: Press **A** or click "Prev" button

### Manage Annotations
- **Add Box**: Click and drag in Edit Mode
- **Remove Box**: Press **Delete** key
- **Select All**: Click "Select All" or press **Ctrl+A**
- **Deselect All**: Click "Deselect All" or press **Ctrl+D**

### Save Work
- **Manual Save**: Click "Save" button or press **S**
- **Auto-Save**: Enable "Auto Save" checkbox to save automatically

## Format Conversion Utilities

The tool includes several utilities to convert your annotation formats. These are located in the control panel on the left.

- **Convert TXT to JSON**: Converts a folder of `.txt` files into individual JSON files.
- **Convert JSON to TXT**: Converts a folder of individual JSON files back into `.txt` format.
- **Convert TXT to COCO**: Converts an entire dataset from `.txt` files into a single `_annotations.coco.json` file.
- **Merge JSON to COCO**: Merges a folder of individual JSON files into a single `_annotations.coco.json` file, which is useful for creating a unified dataset.

These actions create new files and do not modify your original annotations.

## Understanding the Interface

```
┌─────────────────────────────────────────┬──────────────────┐
│  Menu Bar: File | Edit | View | Help    │                  │
├─────────────────────────────────────────┤  Status Bar      │
│  [Load] [Format] [Edit] [View] [A] [D]  │                  │
│  [Save] [Auto Save ☑]                   │  [1/20] mode    │
├────────────────────────┬────────────────┤  [Format: Txt]  │
│                        │ Annotations:   │                  │
│   Image Canvas         │ ☑ Class #0    │                  │
│   (Draw boxes here)    │ ☑ Class #1    │                  │
│                        │ ☐ Class #2    │                  │
│                        │               │                  │
│                        │ [Select All]  │                  │
│                        │ [Deselect All]│                  │
└────────────────────────┴────────────────┴──────────────────┘
```

## Tips for Efficient Annotation

### Speed Up Your Work
1. **Learn Shortcuts**: Memorize A, D, E, V, S, Delete
2. **Use Auto-Save**: Enable it to forget about saving
3. **Batch Process**: Annotate in themes (all cars, then all people)
4. **Select All**: Use Ctrl+A to quickly toggle visibility

### Maintain Quality
1. **Draw Tight Boxes**: Include full object, minimal background
2. **Be Consistent**: Same size boxes for similar objects
3. **Check Your Work**: Use View Mode to review
4. **Fix Errors**: Delete and redraw if needed

### Organize Your Data
1. **File Naming**: Use consistent naming (image_001.jpg with image_001.txt)
2. **Separate Folders**: Keep images and labels in different folders
3. **Classes File**: Keep classes.txt updated with all classes
4. **Backup**: Regularly backup your annotation files

## Troubleshooting

### Application won't start
```bash
# Make sure PyQt5 is installed
pip install --upgrade PyQt5

# Try running with Python 3
python3 main.py
```

### Images not showing
- Verify image folder path is correct
- Check image format is supported (JPG, PNG)
- Ensure file permissions are readable

### Can't draw boxes
- Make sure you're in **Edit Mode** (button shows "View Mode")
- Click and **drag** to draw, don't just click
- Box must be at least 5x5 pixels

### Annotations not saving
- Check that **label folder** is selected
- Verify **format** is selected
- Check disk space available
- Ensure write permissions on folder

## Getting Help

1. **Press F1** to open the comprehensive help dialog
2. **Check tooltips** by hovering over buttons
3. **Read status bar** messages at bottom
4. **Review tips** in Help → Tips & Tricks

## Next Steps

### When You're Ready to Scale Up
1. Learn about different annotation formats
2. Set up batch processing workflow
3. Implement custom export scripts
4. Customize the UI theme

### Advanced Features
- Auto-detect format from existing labels
- Selection memory per image
- Natural image sorting
- Customizable theme colors

## Common Keyboard Shortcuts Reference

```
Navigation:    A (Prev) | D (Next) | F5 (Refresh)
Editing:       E (Edit) | V (View) | Del (Delete) | S (Save)
Selection:     Ctrl+A (All) | Ctrl+D (None)
Help:          F1 (Help) | Esc (Exit)
```

## TXT Format Example

If you choose TXT format, your `.txt` files will look like:

**image_001.txt**:
```
0 0.532 0.421 0.342 0.512
1 0.123 0.789 0.098 0.167
```

Each line: `<class_id> <x_center> <y_center> <width> <height>`

All coordinates are **normalized** (0-1 range).

## File Organization Example

```
my_project/
├── images/
│   ├── image_001.jpg
│   ├── image_002.jpg
│   └── image_003.jpg
└── labels/
    ├── image_001.txt  (created by annotator)
    ├── image_002.txt  (created by annotator)
    └── image_003.txt  (created by annotator)
```

## Quick Reference: What Each Button Does

| Button | Function |
|--------|----------|
| Load Dataset | Opens file browser to select images and labels |
| Select Format | Choose TXT, JSON, or COCO format |
| Edit Mode | Switch to annotation editing mode |
| View Mode | Switch to read-only review mode |
| Prev (A) | Go to previous image |
| Next (D) | Go to next image |
| Save (S) | Save current image annotations |
| Auto Save | Automatically save when navigating |
| Select All | Check all boxes in current image |
| Deselect All | Uncheck all boxes in current image |

## Performance Tips

- For large images (>4000px), resize them first
- Use SSD for better performance than HDD
- Close other applications to free RAM
- Enable auto-save to reduce switching

## Privacy & Security

- All processing is local (no cloud uploads)
- Data stays on your computer
- No internet connection required
- Delete annotations anytime

---

**Ready to start? Press F1 in the application for the full help guide!** 🚀
