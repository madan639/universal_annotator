# User Guide - New Features

## Feature 1: Classes Loaded Dialog

**When it appears:**
- After you load a dataset (click "Load Dataset" and select image/label folders)

**What it shows:**
- List of loaded classes (first 20 shown, with count of remaining)
- Total number of classes
- Message: "If you want to change these classes, click 'Load Different Classes' button above"

**What to do:**
- Click OK to dismiss and continue with annotation
- If you want different classes, click "Load Different Classes" button in the Control Panel

---

## Feature 2: Select Format Dialog

**How to open:**
- Click the **"Select Format"** button in the Control Panel (left sidebar)

**What you see:**
```
┌─────────────────────────────────────────┐
│        Select Format               [X]  │
│                                         │
│  Choose output annotation format:      │
│                                         │
│  [ TXT (.txt) ]  [ JSON (.json) ]      │
│  [ COCO (_annotations.coco.json) ]    │
└─────────────────────────────────────────┘
```

**How to close WITHOUT selecting:**
1. Click the **X** button (top right) - dialog closes
2. Press **ESC** key - dialog closes
3. Press **Q** key - closes entire app (asks for confirmation)

**How to select a format:**
1. Click "TXT (.txt)" → Selects TXT format
2. Click "JSON (.json)" → Selects JSON format
3. Click "COCO (_annotations.coco.json)" → Selects COCO format

---

## Feature 3: Bbox Selection

**How it works:**
- Load a dataset with images and bounding boxes
- In the **Annotations** panel on the right, you'll see a list of detected boxes
- Each box shows: `class_name                    #0`

**To view a single box:**
1. Click "Deselect All" button to hide all boxes
2. Click the checkbox for the box you want to see
3. ✅ The box appears on the image canvas

**To view multiple boxes:**
1. Click checkboxes for boxes you want to see
2. ✅ All checked boxes appear on the image

**To view all boxes:**
1. Click "Select All" button
2. ✅ All boxes appear on the image

---

## Feature 4: Keyboard Shortcuts

### Anywhere in the Application

| Key | Action |
|-----|--------|
| **Q** | Close application (asks for confirmation) |
| **ESC** | Close application (asks for confirmation) |
| **A** | Go to previous image |
| **D** | Go to next image |
| **S** | Save current annotation |
| **DELETE** | Delete last drawn box (Edit Mode only) |

### In Dialog Boxes

| Key/Button | Action |
|-----------|--------|
| **ESC** | Close dialog without selecting |
| **X button** | Close dialog without selecting |
| Click button | Select that option |

---

## Feature 5: Control Panel Layout

```
┌──────────────────────────────┐
│  File Operations             │
│  ┌──────────────────────────┐│
│  │  Load Dataset            ││
│  │  Load Classes from JSON  ││
│  └──────────────────────────┘│
│                              │
│  Mode                        │
│  ┌──────────┬──────────────┐│
│  │Edit Mode │ View Mode    ││
│  └──────────┴──────────────┘│
│                              │
│  Navigation                  │
│  ┌──────────┬──────────────┐│
│  │ Prev (A) │ Next (D)     ││
│  └──────────┴──────────────┘│
│                              │
│  ┌──────────┬──────────────┐│
│  │ Save (S) │Select Format ││  ← NEW BUTTON
│  └──────────┴──────────────┘│
│                              │
│  Current Format: TXT         │
│                              │
│  Format Conversion           │
│  ┌──────────────────────────┐│
│  │Convert TXT to JSON       ││
│  │Convert JSON to TXT       ││
│  │Convert TXT to COCO       ││
│  │Merge JSON to COCO        ││
│  └──────────────────────────┘│
│                              │
│  ☑ Auto Save                 │
│                              │
└──────────────────────────────┘
```

---

## Feature 6: Annotations Panel

```
┌──────────────────────────────┐
│  Annotations                 │
│ [Select All] [Deselect All]  │
│                              │
│ ☑ helmet                  #0 │  ← Can toggle
│ ☑ helmet                  #1 │
│ ☑ helmet                  #2 │
│ ☑ helmet                  #3 │
│ ☑ helmet                  #4 │
│ ☑ helmet                  #5 │
│ ☑ person                  #6 │
│ ☑ person                  #7 │
│ ☑ person                  #8 │
│ ☑ person                  #9 │
│ ☑ person                 #10 │
│ ☑ person                 #11 │
│ ☑ person                 #12 │
│ ☑ safety_vest            #13 │
│ ☑ no_safety_vest         #14 │
│                              │
│        (scroll down)         │
└──────────────────────────────┘
```

**Note:** Index numbers (#0, #1, etc.) are always aligned on the right side for uniform appearance!

---

## Quick Start

1. **Load Dataset**
   - Click "Load Dataset" button
   - Select image folder → Label folder
   - Classes dialog appears → Click OK
   - Format is auto-detected (TXT/JSON/COCO)

2. **View Annotations**
   - All boxes appear by default
   - Uncheck boxes to hide them
   - Check boxes to show them

3. **Edit Mode** (if needed)
   - Click "Edit Mode" button
   - Draw boxes on image (click and drag)
   - Select class when prompted
   - Press DELETE to undo last box
   - Press S to save

4. **Save Work**
   - Press S (or click "Save (S)" button)
   - Annotations automatically saved in label folder

5. **Close App**
   - Press Q or ESC
   - Confirmation dialog appears
   - Click "Yes" to exit

---

## Tips & Tricks

💡 **Tip 1:** Use keyboard shortcuts for speed
- Press D to go next, A to go previous

💡 **Tip 2:** Deselect all boxes to see image clearly
- Click "Deselect All" to hide all boxes
- Click boxes you want to verify

💡 **Tip 3:** Use the format dialog to switch formats
- Click "Select Format" to change TXT → JSON or COCO

💡 **Tip 4:** Check "Auto Save" to save automatically
- Reduces clicks when moving between images

💡 **Tip 5:** Classes are shown on the image
- Each box label shows the class name at top-left

---

## Getting Help

- **Hover over buttons** for tooltips
- **Status bar at bottom** shows current image info
- **Right panel** shows all boxes with checkboxes
- **Format label** shows current annotation format
