# Recent Changes Summary

## 1. ✅ Fixed Bbox Selection Issue
**Problem**: When deselecting all boxes and trying to select a single box, the checkbox wouldn't trigger and the box wouldn't show on the canvas.

**Root Cause**: The `update_labels_panel()` function was using custom widgets (`setItemWidget()`) which broke the standard checkbox interaction and prevented the `itemChanged` signal from firing.

**Solution**: Removed custom widget rendering and returned to using standard `QListWidgetItem` with simple text display, while maintaining uniform spacing using string padding.

**Files Modified**: `core/app_window.py`

---

## 2. ✅ Added Classes Loaded Dialog
**Feature**: When a dataset is loaded, a popup dialog now shows the classes that were loaded from the classes.txt file.

**Implementation**: 
- New function `_show_loaded_classes_dialog()` displays:
  - List of loaded classes (up to 20 shown, with "... and N more" if more than 20)
  - Total class count
  - Instructions to click "Load Different Classes" button if user wants to change classes

**Files Modified**: `core/app_window.py`

---

## 3. ✅ Fixed Select Format Dialog
**Problem**: The Select Format popup had a minimize (`-`) button that shouldn't be there.

**Solution**: Changed window flags to use `Qt.Dialog | Qt.WindowCloseButtonHint` which creates a proper dialog window with only the close (`X`) button visible.

**Keyboard Shortcuts**: 
- `ESC` key: Close app with confirmation dialog ✓
- `Q` key: Close app with confirmation dialog ✓
- These work from anywhere in the app

**Files Modified**: `core/app_window.py`

---

## 4. ✅ Removed Select Format Button from UI
**Change**: The "Select Format" button has been hidden from the control panel to clean up the UI.

**Implementation**: 
- Kept the button in the ControlPanel class for code compatibility
- Set `setVisible(False)` to hide it from the UI
- Button is still functional when called programmatically

**Files Modified**: `ui/components/panels.py`

---

## Files Changed
1. `/universal_annotator/core/app_window.py`
   - Fixed bbox selection mechanism
   - Added class dialog display
   - Improved Select Format dialog
   - Enhanced keyPress event handling

2. `/universal_annotator/ui/components/panels.py`
   - Removed Select Format button from visible UI
   - Cleaned up save/format layout

---

## Key Improvements
✅ Checkbox selection now works properly  
✅ User gets feedback when dataset is loaded  
✅ Select Format dialog is cleaner (no minimize button)  
✅ UI is less cluttered (no Select Format button in panel)  
✅ Keyboard shortcuts (ESC, Q) working to close app  
✅ Classes are displayed with uniform spacing (#N aligned on right)  

