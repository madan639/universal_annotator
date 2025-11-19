# Create Label Files - Feature Flow Diagram

## User Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  User clicks "Load Dataset" button                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Dialog 1: Select Image Folder                                  │
│  User selects: /path/to/images/                                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Dialog 2: Select Label Folder                                  │
│  User selects: /path/to/labels/ (can be EMPTY)                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Format Detection                                                │
│  - If label files exist → Auto-detect format                   │
│  - If NO label files   → Ask user to select format             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Do label files exist?│
         └────┬──────────────┬───┘
              │ YES          │ NO
              │              │
              ▼              ▼
        [Continue]    ┌──────────────────────────────────┐
                      │  Dialog 3: Create Label Files    │
                      │  (NEW FEATURE)                   │
                      │                                  │
                      │  ○ TXT Format                    │
                      │  ○ JSON Format                   │
                      │  ○ COCO Format                   │
                      │                                  │
                      │  [Create Label Files] [Skip]    │
                      └────┬──────────────┬──────────────┘
                           │              │
                     [Click Create] [Click Skip]
                           │              │
                           ▼              ▼
              ┌──────────────────┐  [Continue to next step]
              │ Create Structure │
              │ Initialize Files │
              └────────┬─────────┘
                       │
                       ▼
           ┌─────────────────────────┐
           │ Show Success Message    │
           │ "Label files created"   │
           └────────┬────────────────┘
                    │
                    ▼
         [Continue with annotation]
```

## File Structure Created

### For TXT Format:
```
/path/to/labels/
├── (empty folder, individual .txt files created during annotation)
```

### For JSON Format:
```
/path/to/labels/
├── (empty folder, individual .json files created during annotation)
```

### For COCO Format:
```
/path/to/labels/
├── _annotations.coco.json
    └── {
          "info": {...},
          "licenses": [],
          "images": [],
          "annotations": [],
          "categories": []
        }
```

## Key Features

✅ **Smart Detection**: Only shows dialog when label folder is truly empty
✅ **Format Selection**: User chooses which format to initialize
✅ **COCO Initialization**: Automatically creates proper COCO JSON structure
✅ **Skip Option**: User can skip file creation and proceed anyway
✅ **Success Feedback**: User gets confirmation message
✅ **Error Handling**: Graceful handling if creation fails
✅ **Logging**: All actions logged for debugging

## Code Components

### CreateLabelsDialog Class
- Location: `ui/dialogs/create_labels_dialog.py`
- Responsibilities:
  - Show UI with format options
  - Handle user selection (Create or Skip)
  - Return selected format and action

### create_label_structure() Function
- Location: `ui/dialogs/create_labels_dialog.py`
- Responsibilities:
  - Create label directory
  - Initialize format-specific files
  - Handle errors gracefully
  - Return success/failure status

### Integration in app_window.py
- Location: `core/app_window.py` → `load_dataset()` method
- Responsibilities:
  - Detect if label files exist
  - Show dialog if needed
  - Execute file creation if requested
  - Show success/error messages

## Testing Checklist

- [ ] Load dataset with empty label folder
- [ ] Dialog appears with correct image count
- [ ] TXT format selection works
- [ ] JSON format selection works
- [ ] COCO format creates `_annotations.coco.json`
- [ ] Skip button allows proceeding without creating
- [ ] Success message displays
- [ ] Folder structure is correct
- [ ] Files can be used for annotation
- [ ] Cancel button closes dialog safely
