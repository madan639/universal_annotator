# Bbox Selection Fix - Explanation

## Problem
When you deselected all boxes and tried to select a single box by clicking its checkbox, the box would NOT appear on the canvas. The checkbox appeared to be unresponsive or the display wouldn't update.

## Root Cause
The issue was in the `update_labels_panel()` function in `core/app_window.py`.

### What was happening:
1. Each list item was being rendered with a **custom widget** using `setItemWidget()`
2. This custom widget was a `QHBoxLayout` with labels for the class name and index number
3. When you set a custom widget on a `QListWidgetItem`, the **standard checkbox interaction is disabled**
4. The `itemChanged` signal was not being triggered when clicking the checkbox
5. Therefore, `on_label_toggled()` callback was never called
6. The `canvas.selected_boxes` was never updated
7. The canvas continued to display nothing (since no boxes were selected)

### The Signal Flow (Broken):
```
User clicks checkbox 
    ↓
Custom widget is displayed instead of standard item
    ↓
Checkbox click not properly registered
    ↓
itemChanged signal NOT emitted
    ↓
on_label_toggled() NOT called
    ↓
canvas.selected_boxes NOT updated
    ↓
Canvas shows nothing ❌
```

## Solution
Removed the custom widget rendering and returned to using standard `QListWidgetItem` with simple text.

### Changes Made in `update_labels_panel()`:

**BEFORE (Broken):**
```python
# Create a custom widget for the item
item_widget = QWidget()
item_layout = QHBoxLayout()
item_layout.setContentsMargins(0, 0, 0, 0)
item_layout.setSpacing(5)

class_label = QLabel(class_name)
index_label = QLabel(f"#{idx}")
index_label.setStyleSheet("color: gray;")

item_layout.addWidget(class_label)
item_layout.addStretch()
item_layout.addWidget(index_label)

item_widget.setLayout(item_layout)
self.labels_list.setItemWidget(item, item_widget)  # ❌ BREAKS CHECKBOX!
```

**AFTER (Fixed):**
```python
# Set display text - simple and clean
item.setText(f"{class_name}  #{idx}")
# No setItemWidget() call - checkbox works!
```

### The Signal Flow (Fixed):
```
User clicks checkbox 
    ↓
Standard QListWidgetItem checkbox is interactive
    ↓
Checkbox click properly registered
    ↓
itemChanged signal EMITTED ✓
    ↓
on_label_toggled() CALLED ✓
    ↓
canvas.selected_boxes UPDATED ✓
    ↓
Canvas shows selected bbox ✓
```

## Testing
To verify the fix works:

1. Load a dataset with annotations
2. Click "Deselect All" button - all checkboxes should uncheck
3. Click the checkbox for the first item (e.g., "helmet #0")
4. **Expected behavior**: The corresponding bounding box should appear on the canvas immediately

## Files Modified
- `core/app_window.py` - `update_labels_panel()` function

## Side Benefits
- Simpler code (no custom widget complexity)
- Better performance (less widget creation)
- More consistent with PyQt5 best practices
- Display text is still informative: "ClassName  #Index"
