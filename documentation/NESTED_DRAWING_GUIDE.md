# Nested Box Drawing - Complete Setup Guide

## Current Implementation Status
✅ Code is in place for nested drawing with these features:
- When Drawing Mode (M key) is ENABLED and you click inside a box, a new box is drawn inside it
- The new box is constrained (clamped) to stay within the parent box bounds
- Parent box remains visible while you draw the child
- Mouse preview (green box) shows the nested box you're creating

## Step-by-Step Test

### 1. Launch App
```bash
cd /home/madan/Documents/person_project/annotation_tool/universal_annotator
python3 app.py 2>&1 | tee app.log
```

### 2. Load Dataset  
- Click "Load Dataset" button
- Select folder with images
- Select folder with labels (or empty if first time)
- Wait for first image to load

### 3. Create Parent Box (if not already there)
- Make sure you're in **Edit Mode** (status bar shows blue "EDIT MODE")
- Press **M** to enable Drawing Mode (status bar shows "Drawing mode enabled")
- Click and drag on image to create a large box (e.g., covering half the image)
- Select class when dialog appears (e.g., "person")
- Box is now saved

### 4. Test Nested Drawing ⭐
- Image should still be displayed with the person box visible
- Status bar should show "Drawing mode enabled" still
- **NOW CLICK INSIDE THE PERSON BOX and drag**
  - You should see a GREEN preview box that stays within the person box
  - As you drag, the green box should resize
- Release mouse
- Class selection dialog appears
- Choose a class (e.g., "helmet", "safety_vest")
- New box appears INSIDE the person box ✓

## What To Watch In Console Logs

### When you click inside the person box:
```
[NESTED_DRAW] ======== MOUSE PRESS ========
[NESTED_DRAW] mode=edit, image_loaded=True, is_drawing_enabled=True, num_boxes=1
[NESTED_DRAW] Click at img_coords=(123, 456)
[NESTED_DRAW] Found 1 boxes under cursor
[NESTED_DRAW] Best box: idx=0, bounds=(10, 20, 300, 400), is_drawing_enabled=True
[NESTED_DRAW] ✓ STARTING NESTED DRAW - parent_box_index=0, parent_box_bounds=(10, 20, 300, 400)
```

### When you drag mouse:
```
[NESTED_DRAW] mouseMoveEvent: parent_box_bounds=(10, 20, 300, 400), start=(123, 456), current=(130, 460)
[NESTED_DRAW] Clamped: x1=123, y1=456, x2=130, y2=460
[NESTED_DRAW] current_box set to (123, 456, 7, 4)
```

### When you release mouse:
```
(Class selection dialog appears)
```

## Troubleshooting

### Problem: "Not in drawing mode" appears in logs
**Solution:** You forgot to press **M** after going to Edit Mode
- Press **M** once
- Status bar should change to "Drawing mode enabled"
- Try again

### Problem: "Found 0 boxes under cursor"
**Solution:** You're clicking outside the person box
- Make sure you click DIRECTLY INSIDE the person box boundaries
- Try clicking near the center of the person box

### Problem: No green preview appears
**Solution:** Check that:
1. Drawing mode IS on (M was pressed)
2. You clicked inside a box (logs should show parent_box_bounds)
3. Try dragging further (preview might be tiny if you don't drag far)

### Problem: Drawing creates a box OUTSIDE the person box
**Solution:** This shouldn't happen with the clamping logic
- Check logs for "Clamped:" line
- If no clamping appears, drawing mode might have turned off during drag
- Re-enable by pressing **M**

## Reset If Stuck
1. Press **X** to disable drawing mode
2. Press **M** to re-enable it  
3. Try the test again

## Expected Result
After completing the test, you should have:
- 1 person box (larger, covers ~half the image)
- 1 nested box inside it (smaller, represents helmet/vest)
- Both boxes saved in the annotation file
