# Quick Reference: Create Label Files Feature

## 🎯 What's New?

When you load a dataset with an **empty label folder**, the app now offers to create label files automatically!

## 🔄 User Flow

```
Load Dataset → Select Images → Select Labels (empty)
    ↓           ↓               ↓
             Auto-detect format
                 ↓
            No files found?
                 ↓ YES
    ┌──────────────────────────┐
    │ Dialog: Create Label Files│
    │ ○ TXT                    │
    │ ○ JSON                   │
    │ ○ COCO                   │
    │ [Create] [Skip]         │
    └────┬─────────────────────┘
         │
    [User chooses]
         │
    ✅ SUCCESS → Continue
```

## 📦 What Gets Created

### TXT Format
- Label folder (empty, files created as you annotate)

### JSON Format  
- Label folder (empty, files created as you annotate)

### COCO Format
- Label folder
- **_annotations.coco.json** (initialized with proper structure)

## 🎮 How to Use

1. **Click "Load Dataset"**
2. **Select your images folder**
3. **Select an EMPTY labels folder**
4. **Dialog appears** (only if folder is empty)
   - Choose format: TXT, JSON, or COCO
   - Click **"Create Label Files"** or **"Skip"**
5. **Done!** You can now annotate

## ✅ Success Message

```
✓ Label files created successfully for [FORMAT] format.
  You can now start annotating your images.
```

## 🚫 When Dialog Does NOT Appear

- ✗ Label folder already has files
- ✗ User selects an existing dataset with annotations

## 🎲 Options

### Option 1: Create Label Files
- System creates folder structure
- Initializes format-specific files
- You can immediately start annotating

### Option 2: Skip
- Dialog closes
- Continue without creating files
- You can create files later manually

## 💡 Pro Tips

1. **COCO Format** is best for large datasets (single JSON file for all)
2. **TXT Format** is best for per-image annotations (one file per image)
3. **JSON Format** is flexible and human-readable
4. You can **skip** dialog and create files later if unsure

## 🔍 Where to Find Files

After creation, your label folder will have:

**TXT/JSON:**
```
labels/
├── (empty initially, files appear as you annotate)
```

**COCO:**
```
labels/
├── _annotations.coco.json  ← This file is created!
```

## 📋 Supported Formats

| Format | File Type | Use Case |
|--------|-----------|----------|
| **TXT** | `.txt` | Per-image labels (YOLO style) |
| **JSON** | `.json` | Per-image flexible format |
| **COCO** | `_annotations.coco.json` | Unified single file |

## ⚙️ Technical Details

**Files Involved:**
- `ui/dialogs/create_labels_dialog.py` - Dialog UI
- `core/app_window.py` - Integration (load_dataset method)

**Key Functions:**
- `CreateLabelsDialog` - Shows format selection
- `create_label_structure()` - Creates files/folders

## 🆘 Troubleshooting

**Q: Dialog doesn't appear?**
A: Make sure your label folder is truly empty. If it has any files, the dialog won't show.

**Q: Can I change format later?**
A: Yes, just click "Format" button to select a different format and reload.

**Q: What if creation fails?**
A: You'll see a warning, but can still continue. Manually create files if needed.

**Q: Can I undo creation?**
A: Yes, just delete the created files/folders and reload the dataset.

## 📞 Need Help?

- Check if label folder is empty
- Try skipping the dialog and creating files manually
- Check the log file for error messages
- Reload the dataset to try again

---

**Version:** 1.0  
**Status:** ✅ Ready to Use  
**Last Updated:** 2024-11-19
