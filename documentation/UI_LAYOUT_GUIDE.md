# Universal Annotator - UI Layout Guide

## Application Window Layout

```
┌────────────────────────────────────────────────────────────────────┐
│ Universal Annotator Tool                                    _ □ × │
├─────────────────────────────────────────────────────────────────────┤
│ File    Edit    View    Help                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ ┌──────────────────────────────┬─────────────────────────────────┐ │
│ │ CONTROLS (Left Sidebar)      │ CANVAS (Center)                 │ │
│ ├──────────────────────────────┤                                 │ │
│ │                              │                                 │ │
│ │ File Operations:             │                                 │ │
│ │ [Load Dataset]               │       Image Display Area        │ │
│ │                              │                                 │ │
│ │ Mode:                        │                                 │ │
│ │ [Edit Mode] [View Mode]      │     Click & Drag to Draw       │ │
│ │                              │     Bounding Boxes              │ │
│ │ Navigation:                  │                                 │ │
│ │ [Prev (A)] [Next (D)]        │                                 │ │
│ │                              │                                 │ │
│ │ Actions:                     │                                 │ │
│ │ [Save (S)] [Select Format]   │                                 │ │
│ │                              │                                 │ │
│ │ Auto Save ☑                  │                                 │ │
│ │                              │                                 │ │
│ └──────────────────────────────┼─────────────────────────────────┤
│                                │ LABELS PANEL (Right Sidebar)    │
│                                ├─────────────────────────────────┤
│                                │ Annotations                     │
│                                │ [Select All] [Deselect All]    │
│                                │                                 │
│                                │ ☑ person #0                    │
│                                │ ☑ car #1                       │
│                                │ ☐ bicycle #2                   │
│                                │ ☑ dog #3                       │
│                                │                                 │
│                                │ (scrollable list)               │
│                                └─────────────────────────────────┘
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│ [5/20] image_005.jpg | Boxes: 3 | EDIT MODE | Format: TXT        │
└─────────────────────────────────────────────────────────────────────┘
```

## Menu Bar Structure

### File Menu
```
File
├─ Load Dataset          Ctrl+O
├─ Select Format
├─ ─────────────
├─ Save                  Ctrl+S
├─ ─────────────
└─ Exit                  Ctrl+Q
```

### Edit Menu
```
Edit
├─ Edit Mode             E
├─ View Mode             V
├─ ─────────────
├─ Delete Last Box       Del
├─ ─────────────
├─ Select All Boxes      Ctrl+A
└─ Deselect All Boxes    Ctrl+D
```

### View Menu
```
View
├─ Previous Image        A
├─ Next Image            D
├─ ─────────────
├─ Refresh Current Image F5
├─ ─────────────
└─ Toggle Auto-Save
```

### Help Menu
```
Help
├─ Help & Shortcuts      F1
├─ ─────────────
└─ About
```

## Control Panel (Left Sidebar)

```
┌─────────────────────────────┐
│ File Operations             │
├─────────────────────────────┤
│ [     Load Dataset     ]    │
│                             │
│ Mode                        │
├─────────────────────────────┤
│ [  Edit Mode  ][View Mode ] │
│                             │
│ Navigation                  │
├─────────────────────────────┤
│ [ Prev (A) ][ Next (D) ]   │
│                             │
│ Actions                     │
├─────────────────────────────┤
│ [   Save (S)  ]             │
│ [Select Format ]            │
│                             │
│ ☑ Auto Save                 │
│                             │
└─────────────────────────────┘
```

## Labels Panel (Right Sidebar)

```
┌──────────────────────────────┐
│ Annotations                  │
├──────────────────────────────┤
│ [Select All] [Deselect All] │
├──────────────────────────────┤
│ ☑ person #0                  │
│ ☑ car #1                     │
│ ☑ bicycle #2                 │
│ ☐ dog #3                     │
│ ☑ cat #4                     │
│ (scrollable)                 │
│                              │
└──────────────────────────────┘
```

## Status Bar (Bottom)

```
┌────────────────────────────────────────────────────────────────┐
│ EDIT MODE | [5/20] image_005.jpg | Boxes: 3 | Format: TXT   │
└────────────────────────────────────────────────────────────────┘
```

Components:
- Mode indicator (EDIT MODE / VIEW MODE)
- Image info (Position/Total) Filename
- Box count
- Format name

## Color Scheme

### Dark Theme (Default)
```
Primary Background:     #1e1e2e  (Dark gray-blue)
Secondary Background:   #2d2d44  (Slightly lighter)
Accent Color:           #00bfff  (Bright cyan)
Text Primary:           #ffffff  (White)
Text Secondary:         #b0b0b0  (Light gray)
Border:                 #404040  (Dark border)
Success:                #00ff00  (Green)
Warning:                #ff9800  (Orange)
Danger:                 #ff4444  (Red)
```

### Light Theme
```
Primary Background:     #ffffff  (White)
Secondary Background:   #f5f5f5  (Light gray)
Accent Color:           #0078d4  (Blue)
Text Primary:           #000000  (Black)
Text Secondary:         #666666  (Gray)
Border:                 #d0d0d0  (Light border)
Success:                #107c10  (Green)
Warning:                #ff9800  (Orange)
Danger:                 #d13438  (Red)
```

## Help Dialog (F1)

### Getting Started Tab
```
Getting Started with Universal Annotator

1. Basic Workflow
   - Load Dataset
   - Select Format
   - Switch to Edit Mode
   - Draw Bounding Boxes
   - Select Class
   - Navigate
   - Save

2. Supported Formats
   - TXT (.txt)
   - JSON (.json)
   - COCO (_annotations.coco.json)

3. Modes
   - View Mode: Read-only
   - Edit Mode: Add/Modify
```

### Keyboard Shortcuts Tab
```
Navigation           Editing
A - Previous        E - Edit Mode
D - Next            V - View Mode
← → - Navigate      Del - Delete Box
                    S - Save

Selection           General
Ctrl+A - All        F1 - Help
Ctrl+D - None       F5 - Refresh
                    Esc - Exit
```

### Tips & Tricks Tab
```
Efficient Annotation
- Use keyboard shortcuts
- Enable auto-save
- Batch by object type

Best Practices
- Draw tight boxes
- Be consistent
- Review work

Troubleshooting
- Check folder paths
- Verify file formats
- Check permissions
```

## About Dialog

```
┌──────────────────────────────────┐
│     Universal Annotator          │
│          Version 1.0.0           │
│                                  │
│  A comprehensive image           │
│  annotation tool with bounding   │
│  box support for multiple        │
│  annotation formats.             │
│                                  │
│  Features:                       │
│  • Multiple formats              │
│  • Keyboard shortcuts            │
│  • Auto-save support             │
│  • Dark/Light themes             │
│                                  │
│  Built with:                     │
│  PyQt5 • OpenCV • NumPy          │
│                                  │
│          [Close]                 │
└──────────────────────────────────┘
```

## Class Selection Dialog

```
┌────────────────────────────────┐
│ Select Class for Bounding Box  │
├────────────────────────────────┤
│                                │
│ Select the class for this      │
│ bounding box:                  │
│                                │
│ [v] person                     │
│     car                        │
│     bicycle                    │
│     dog                        │
│     cat                        │
│                                │
│        [OK]     [Cancel]       │
│                                │
└────────────────────────────────┘
```

## Tooltip Examples

Button: Load Dataset
Tooltip: "Click to load image and label folders"

Button: Edit Mode
Tooltip: "Switch to Edit Mode to create and modify annotations"

Button: Save (S)
Tooltip: "Save current image annotations (Press S)"

Button: Select All
Tooltip: "Select all bounding boxes in current image"

## Keyboard Shortcut Reference Card

```
╔════════════════════════════════════════╗
║  UNIVERSAL ANNOTATOR QUICK REFERENCE   ║
╠════════════════════════════════════════╣
║ NAVIGATION                             ║
║  A - Previous Image                    ║
║  D - Next Image                        ║
║  F5 - Refresh                          ║
║                                        ║
║ EDITING                                ║
║  E - Edit Mode                         ║
║  V - View Mode                         ║
║  Delete - Remove Last Box              ║
║  S - Save                              ║
║                                        ║
║ SELECTION                              ║
║  Ctrl+A - Select All                   ║
║  Ctrl+D - Deselect All                 ║
║                                        ║
║ HELP & EXIT                            ║
║  F1 - Help Dialog                      ║
║  Esc - Exit                            ║
╚════════════════════════════════════════╝
```

## Status Bar States

### View Mode
```
VIEW MODE | [1/10] image_001.jpg | Boxes: 5 | Format: TXT
```

### Edit Mode
```
EDIT MODE | [1/10] image_001.jpg | Boxes: 5 | Format: TXT
```

### Loading
```
Please wait... | Boxes: 0 | Format: -
```

## Button Styles

### Standard Button
```
┌────────────────┐
│  Load Dataset  │
└────────────────┘
Gray background, white text
```

### Accent Button (Primary Action)
```
┌────────────┐
│    OK      │
└────────────┘
Cyan background, white text
```

### Hover State
```
┌────────────────┐
│  Load Dataset  │  ← Border highlights
└────────────────┘
```

### Disabled State
```
┌────────────────┐
│  Load Dataset  │  ← Grayed out
└────────────────┘
```

## Window Resizing

The layout is responsive:
- **Canvas**: Expands/shrinks with window
- **Left Panel**: Fixed width (280px)
- **Right Panel**: Fixed width (280px)
- **Menu & Status**: Always visible
- **Minimum Size**: 1024x600

## Responsive Behavior

```
Wide Monitor (1920x1080)
├─ Left Panel (280px)
├─ Canvas (1200px) ← Large display area
└─ Right Panel (280px)

Narrow Monitor (1024x768)
├─ Left Panel (280px)
├─ Canvas (400px) ← Smaller display area
└─ Right Panel (280px)
```

---

**Note**: This is the layout for the dark theme. Light theme uses the same layout with different colors.
