# 📁 Converter Output Folders - Summary

## Overview
All 6 converter functions now automatically create organized output folders instead of requiring user input for folder selection. This makes the workflow much cleaner and more organized.

---

## Folder Structure

When you perform a conversion, the output will be automatically saved in the following folders:

### 1. **TXT → JSON Conversion**
- **Function:** `convert_yolo_to_json()`
- **Output Folder:** `converted_json/`
- **Location:** Created in the TXT label directory
- **Files:** Per-image JSON files (one per image)

### 2. **JSON → TXT Conversion**
- **Function:** `convert_json_to_yolo()`
- **Output Folder:** `converted_txt/`
- **Location:** Created in the JSON label directory
- **Files:** Per-image TXT files in YOLO format

### 3. **TXT → COCO JSON Conversion**
- **Function:** `convert_yolo_to_coco()`
- **Output Folder:** `converted_coco_json/`
- **Location:** Created in the TXT label directory
- **Files:** Single `_annotations.coco.json` file

### 4. **JSON → COCO JSON (Merge)**
- **Function:** `convert_json_folder_to_coco()`
- **Output Folder:** `converted_coco_json/`
- **Location:** Created in the JSON label directory
- **Files:** Single `_annotations.coco.json` file + `classes.txt`

### 5. **COCO JSON → JSON Conversion**
- **Function:** `convert_coco_to_json_folder()`
- **Output Folder:** `converted_json/`
- **Location:** Created in the same directory as the COCO JSON file
- **Files:** Per-image JSON files + `classes.txt`

### 6. **COCO JSON → TXT Conversion**
- **Function:** `convert_coco_to_yolo()`
- **Output Folder:** `converted_txt/`
- **Location:** Created in the same directory as the COCO JSON file
- **Files:** Per-image TXT files in YOLO format + `classes.txt`

---

## Example Directory Tree

```
my_dataset/
├── images/
│   ├── img1.jpg
│   ├── img2.jpg
│   └── ...
├── labels/
│   ├── img1.txt
│   ├── img2.txt
│   ├── ...
│   ├── converted_json/          ← TXT → JSON output
│   │   ├── img1.json
│   │   ├── img2.json
│   │   └── ...
│   ├── converted_coco_json/     ← TXT → COCO output
│   │   └── _annotations.coco.json
│   └── converted_txt/           ← JSON → TXT output
│       ├── img1.txt
│       ├── img2.txt
│       └── ...
```

---

## Code Changes

### Converter Functions Updated
✅ `converters/json_to_txt.py` - `convert_json_to_yolo()`
✅ `converters/txt_to_json_converter.py` - `convert_yolo_to_json()`
✅ `converters/txt_to_annotaion_coco_json.py` - `convert_yolo_to_coco()`
✅ `converters/coco_to_json_converter.py` - `convert_coco_to_json_folder()`
✅ `converters/coco_to_txt_converter.py` - `convert_coco_to_yolo()`
✅ `converters/json_to_coco_merge.py` - `convert_json_folder_to_coco()`

### Main Window Updated
✅ `core/app_window.py` - All conversion methods updated to use default folders
- Removed file dialog popups for folder selection
- Now use automatic folder creation
- Display results message shows the output folder path

---

## How It Works

### Before (Old Way)
```python
output_dir = QFileDialog.getExistingDirectory(self, "Select Output Folder")  # User selects folder
if not output_dir:
    return
convert_yolo_to_json(input_dir, output_dir)  # Must pass explicit folder
```

### After (New Way)
```python
convert_yolo_to_json(input_dir, output_dir=None)  # Pass None or omit parameter
# Automatically creates: input_dir/converted_json/
```

---

## Benefits

✅ **No more folder selection dialogs** - Faster workflow
✅ **Organized outputs** - All conversions go to clearly named folders
✅ **Backward compatible** - Can still pass custom folders if needed
✅ **Consistent naming** - Same folder names across all conversions
✅ **Easy to find results** - Always in predictable locations

---

## API Usage

### Example 1: Convert TXT to JSON
```python
from converters.txt_to_json_converter import convert_yolo_to_json

# Automatically creates "converted_json" folder in label_dir
convert_yolo_to_json("/path/to/labels")
# Output: /path/to/labels/converted_json/
```

### Example 2: Convert JSON to COCO (with custom output)
```python
from converters.json_to_coco_merge import convert_json_folder_to_coco

# Still supports custom output path if needed
convert_json_folder_to_coco(
    json_folder="/path/to/json",
    images_folder="/path/to/images",
    output_path="/custom/output/path.json"  # Optional
)
```

### Example 3: Convert COCO to TXT
```python
from converters.coco_to_txt_converter import convert_coco_to_yolo

# Automatically creates "converted_txt" folder next to COCO file
convert_coco_to_yolo("/path/to/coco_file.json")
# Output: /path/to/converted_txt/
```

---

## Implementation Details

All converters check for `None` parameter and auto-create the appropriate folder:

```python
def convert_function(input_path, output_dir=None, ...):
    # Create default output folder if not specified
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(input_path),  # or input_path if it's a dir
            "converted_[format]"
        )
    
    os.makedirs(output_dir, exist_ok=True)
    # ... rest of conversion logic
```

---

## Testing

To test the new functionality:

1. Load a dataset in the annotator tool
2. Click "Convert TXT to JSON" or any other conversion button
3. Result message will show the output folder path like:
   ```
   Successfully converted 5 files to JSON format.
   Output: /path/to/labels/converted_json
   ```

✅ All conversions automatically create appropriately named folders!
