# Universal Annotator

A professional, modern, and powerful image annotation tool designed for creating bounding box annotations with maximum efficiency. It supports multiple formats, features an intelligent and rich user interface, and is packed with advanced features like nested annotations and extensive keyboard shortcuts.

![Universal Annotator UI](assets/icons/image.png)

## Key Features

### Core Features
- **Multiple Export Formats**: Save annotations in **TXT**, **JSON**, and **COCO** formats.
   - Converters and exporters now use dedicated output folders by default (for example: `converted_txt/`, `converted_json/`, `converted_coco_json/`) to avoid overwriting root label files.
- **Dual Annotation Modes**:
    - **Edit Mode**: For creating, and modifying annotations.
    - **View Mode**: A read-only mode for safe reviewing.
- **Advanced Editing**: Interactively move and resize any bounding box using intuitive drag handles.
- **Nested Annotations**: Create bounding boxes inside existing ones, perfect for annotating objects within objects.
- **Intelligent Image Sorting**: Uses natural sorting to correctly order files like `image_2.jpg` before `image_10.jpg`.
- **Selection Memory**: Remembers which bounding boxes were selected for each image, restoring them when you navigate back.
- **Auto-Save**: Automatically saves your work when you move to the next or previous image, preventing data loss.
- **Format Auto-Detection**: Automatically detects the annotation format from existing label files in the selected directory.
- **JSON Class Discovery**: Intelligently scans your JSON files to discover class names, prompting you to confirm and apply them automatically.

### UI Features 
- **Professional Dark Theme**: A beautiful dark theme for user comfort.
- **Mouse Wheel Zoom**: Zoom in and out of images effortlessly using the mouse wheel.
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
python app.py
```

## Usage

### Basic Workflow

1. **Load Data**
   - Click **"Load Dataset"** to select your image and label folders.
   - The annotation format is auto-detected. If no labels exist, you can select a format manually.
   - By default, the app supports JPG, PNG, BMP, TIFF, and WebP image formats.
   - By default, the app looks for label files in the selected label folder that match the image filenames. The Default format is TXT.
   - you can change the format later if needed.

2. **Annotate Images**
   - Press **E** to enter **Edit Mode**.
   - Press **M** to enter **Drawing Mode**. The status bar will confirm you can now draw.
   - Click and drag on the image to draw a bounding box.
   - Select the appropriate class from the dialog that appears.
   - Use **A/D** or the **Previous/Next** buttons to navigate between images.

3. **Annotate Images**
   - Switch to Edit Mode
   - Click and drag to draw bounding boxes
   - Select class when prompted
   - Use A/D or Previous/Next to navigate
   - Click and drag on the image to draw a new bounding box.
   - Select a class for the new box from the dialog that appears.
   - To remove a box, select it in the right-hand panel and click the "Delete Selected" button or press the `Delete` key.

3. **Edit Annotations**
   - In **Edit Mode** (but not Drawing Mode), click on a box to select it.
   - Drag the handles to resize it or drag the box itself to move it.
   - To create a box inside another, press **M** and draw within the parent box.
   - Press **Delete** to remove any selected boxes.

4. **Save Your Work**
   - Press **S** to save manually.
   - Enable the **"Auto Save"** checkbox to save automatically every time you switch images.
   - The status bar will confirm when annotations are saved.

### Supported Annotation Formats

#### TXT Format (.txt files)
```
<class_id> <x_center> <y_center> <width> <height>
0 0.5 0.5 0.3 0.4
1 0.2 0.7 0.2 0.3
```
Note: TXT files use normalized center-based coordinates (xc, yc, w, h) in the 0..1 range. The app's TXT loader converts these to pixel coordinates when displaying on the canvas.

#### JSON Format
```json
{
  "annotations": [
    {"bbox": [x, y, w, h], "category_id": 0},
    {"bbox": [x, y, w, h], "category_id": 1}
  ]
}
``` 
Note: The JSON loader is highly flexible. It automatically detects and parses various structures, including `objects` or `annotations` arrays, and can even extract class names from keys like `className`, `label`, or `category`. It also auto-detects and converts normalized coordinates to pixel values.

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
### keyboard Shortcuts
Press D for Next
A for Previous
S for Save 
E for Edit Mode
V for View Mode
M for makeing bboxes in Edit Mode
X for Exiting From making Bboxes and Edit the Previous Bboxes

###


### Default Settings
Edit `utils/config.py` for:
- Default colors
- Line widths
- Application name and version

## Converters & Export Folders

- By default conversion commands write outputs into a `converted_*` subfolder in the same label/input folder. Examples:
   - TXT conversion output → `converted_txt/`
   - JSON conversion output → `converted_json/`
   - COCO merge/convert output → `converted_coco_json/_annotations.coco.json`

- This prevents accidental creation or overwriting of a root-level `_annotations.coco.json` unless you explicitly save/export to the label folder.

## Notes about COCO files

- The application uses a single COCO JSON file structure when saving/loading COCO datasets. Converter utilities create a `converted_coco_json/_annotations.coco.json` by default. The app may also create or update a `_annotations.coco.json` in a label folder when saving annotations in COCO mode or when using certain exporters — be aware of which folder you are saving to if you want to keep converted outputs separated.

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

- **No Label Editing**: The class label of an existing bounding box cannot be changed. To change a label, you must delete the box and recreate it.
- Single object per box (no segmentation)
- Rectangular boxes only (no rotated or polygonal annotations)

## Future Enhancements

- **In-place Label Editing**: Ability to change the class of an existing bounding box without deleting it.
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

## Author 
Madan Mohan Jha