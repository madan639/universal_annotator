# Create Label Files Feature

## Overview
When a user selects an image folder and an empty label folder, they are now presented with a dialog to create label files in their chosen format (TXT, JSON, or COCO).

## User Flow

### Step 1: User clicks "Load Dataset"
- Selects Image Folder
- Selects Label Folder (can be empty)

### Step 2: Format Detection
- If label files exist → Auto-detect format
- If no label files exist → Ask user to select format

### Step 3: Create Label Files Dialog (NEW)
**Triggered when:** No label files exist in the selected label folder
**Shows:** A dialog with 3 format options:
- ✓ TXT Format (.txt files)
- ✓ JSON Format (.json files)
- ✓ COCO Format (_annotations.coco.json)

**User can:**
- Select a format
- Click "Create Label Files" → Creates folder structure and initializes files
- Click "Skip" → Continue without creating (user can create files later)

## What Gets Created

### TXT Format
- Creates label folder (if doesn't exist)
- Individual .txt files will be created as user annotates each image

### JSON Format
- Creates label folder (if doesn't exist)
- Individual .json files will be created as user annotates each image

### COCO Format
- Creates label folder (if doesn't exist)
- Creates `_annotations.coco.json` file with empty structure:
```json
{
  "info": {
    "description": "Dataset for annotation",
    "version": "1.0",
    "year": 2024
  },
  "licenses": [],
  "images": [],
  "annotations": [],
  "categories": []
}
```

## Files Modified

### Created
- `ui/dialogs/create_labels_dialog.py` - New dialog component

### Updated
- `ui/dialogs/__init__.py` - Export new dialog
- `core/app_window.py` - Import dialog and add creation logic in `load_dataset()`

## Implementation Details

### CreateLabelsDialog Class
Located in: `ui/dialogs/create_labels_dialog.py`
- Shows format selection UI
- Returns (create_files: bool, selected_format: str)

### create_label_structure() Function
Located in: `ui/dialogs/create_labels_dialog.py`
- Handles actual file/folder creation
- Supports all three formats
- Returns success/failure status

### Integration in app_window.py
Located in: `core/app_window.py` → `load_dataset()` method
- Checks if label folder is empty
- If empty, shows CreateLabelsDialog
- Creates files if user confirms
- Shows success message to user

## Example Workflow

```
User → Load Dataset → Select Image Folder (10 images)
                   → Select Empty Label Folder
                   → [Dialog appears: "Create Label Files?"]
                   → User selects "COCO Format"
                   → User clicks "Create Label Files"
                   → System creates:
                      - /labels_folder/_annotations.coco.json (empty COCO structure)
                      - Shows success message
                   → Continue with annotation
```

## Status Messages
- "Created label files for TXT format."
- "Created label files for JSON format."
- "Created label files for COCO format."

## Error Handling
- If creation fails, logs warning and continues
- User can manually create files later using other tools
- Skip option always available to proceed without creating files
