# Universal Annotator

A professional, modern, and comprehensive image annotation tool for creating bounding box annotations. It supports multiple export formats, features a rich user interface with a dark theme, and is designed for an efficient workflow with extensive keyboard shortcuts.

![Universal Annotator UI](assets/icons/image.png)

## Features

### Core Features
- **Multiple Export Formats**: Save annotations in **TXT**, **JSON**, and **COCO** formats.
- **Dual Annotation Modes**:
    - **Edit Mode**: For creating, and modifying annotations.
    - **View Mode**: A read-only mode for safe reviewing.
- **Intelligent Image Sorting**: Uses natural sorting to correctly order files like `image_2.jpg` before `image_10.jpg`.
- **Selection Memory**: Remembers which bounding boxes were selected for each image, restoring them when you navigate back.
- **Auto-Save**: Automatically saves your work when you move to the next or previous image, preventing data loss.
- **Format Auto-Detection**: Automatically detects the annotation format from existing label files in the selected directory.

### UI Features 
- **Professional Dark Theme**: A beautiful dark theme for user comfort.
- **Complete Menu Bar**: A full menu bar provides access to all application features.
- **Rich Status Bar**: Get real-time feedback on the current image, box count, annotation format, and operational mode.
- **Comprehensive Help System**: An in-app help dialog (**F1**) provides a getting started guide, a full list of keyboard shortcuts, and annotation tips.
- **Informative Tooltips**: Hover over any button or control to see a helpful tooltip explaining its function.
- **Extensive Keyboard Shortcuts**: Designed for power users to annotate quickly and efficiently without relying on the mouse.

## Installation

### 1. (Recommended) Create a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Application
```bash
python main.py
```

## Usage

### Basic Workflow

1. **Load Dataset**
   - Click "Load Dataset" button
   - Select folder with images
   - Select folder with labels
   - Format is auto-detected or you can select manually

2. **Choose Annotation Format**
   - **TXT**: Normalized bounding box coordinates in .txt files
   - **JSON**: Custom format with absolute coordinates
   - **COCO**: COCO-format JSON with multiple images

3. **Annotate Images**
   - Switch to Edit Mode
   - Click and drag to draw bounding boxes
   - Select class when prompted
   - Use A/D or Previous/Next to navigate

4. **Save Annotations**
   - Click Save button or press S
   - Auto-save keeps changes synchronized
   - Status bar shows save confirmation

### Supported Annotation Formats

#### TXT Format (.txt files)
```
<class_id> <x_center> <y_center> <width> <height>
0 0.5 0.5 0.3 0.4
1 0.2 0.7 0.2 0.3
```

#### JSON Format
```json
{
  "annotations": [
    {"bbox": [x, y, w, h], "category_id": 0},
    {"bbox": [x, y, w, h], "category_id": 1}
  ]
}
```

#### COCO Format
Standard COCO dataset format with images and annotations arrays.

## Configuration

### Classes
Edit `sample_classes/classes.txt` to define annotation classes:
```
person
car
bicycle
dog
cat
```

### Theme
Edit `main.py` to switch themes:
```python
theme_manager = ThemeManager("dark")  
```

### Default Settings
Edit `utils/config.py` for:
- Default colors
- Line widths
- Application name and version

## Documentation

- **[UI_IMPROVEMENTS.md](UI_IMPROVEMENTS.md)**: Complete UI feature guide
- **[CONTRIBUTING_UI.md](CONTRIBUTING_UI.md)**: Development and contribution guide
- **Help Dialog (F1)**: In-app help with shortcuts and tips

## Troubleshooting

### Images not loading
- Verify image folder path
- Ensure files are supported formats (JPG, PNG, BMP)
- Check file permissions

### Labels not found
- Select annotation format manually
- Ensure label files are in selected folder
- Verify label filenames match image filenames

### Keyboard shortcuts not working
- Ensure application window has focus
- Check Edit/View mode is appropriate
- Verify shortcuts aren't conflicting with system shortcuts

## System Requirements

- Python 3.7+
- PyQt5 5.12+
- OpenCV 4.0+
- NumPy

## Dependencies

See `requirements.txt` for complete list:
- PyQt5: GUI framework
- opencv-python: Image processing
- numpy: Numerical operations

## Performance Tips

- Use images with reasonable resolution (1920x1080 or less)
- Disable unnecessary overlays in View mode
- Enable auto-save to reduce manual saving
- Use keyboard shortcuts for faster workflow
- Clear selections to reduce visual clutter

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff, .tif)
- WebP (.webp)

## Known Limitations

- Single object per box (no segmentation)
- Rectangular boxes only (no rotated or polygonal annotations)
- COCO format uses single file for all images
- Maximum box size limited by image dimensions

## Future Enhancements

- Polygon and segmentation support
- Keyboard shortcut customization
- Additional export formats
- Batch annotation tools
- Statistics and analytics dashboard
- Undo/Redo functionality
- Plugin system

## Contributing

Contributions are welcome! Please see [CONTRIBUTING_UI.md](CONTRIBUTING_UI.md) for:
- Development setup
- Code style guidelines
- Component development
- Testing procedures
- Pull request guidelines

## License

[Add your license information here]

## Support

- **Report Bugs**: Open an issue with steps to reproduce
- **Suggest Features**: Use feature request template
- **Ask Questions**: Check documentation and Help dialog first

## Credits

Built with:
- PyQt5 - GUI Framework
- OpenCV - Image Processing
- NumPy - Numerical Computing

## Version

Current Version: 1.0.0

Last Updated: November 2025
# universal_annotator
# universal_annotator
