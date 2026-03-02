import os
import json
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget, 
    QFormLayout, QLineEdit, QHBoxLayout, QPushButton, 
    QDialogButtonBox
)
from PyQt5.QtCore import QTimer

class ClassManager:
    def __init__(self, path="sample_classes/classes.txt"):
        self.path = path
        # Do not auto-create file here; let the app handle the prompt.
        self.load_classes()

    def load_classes(self):
        # Support multiple formats: txt (one class per line) or json
        if not os.path.exists(self.path):
            self.classes = []
            return

        if self.path.lower().endswith('.json'):
            try:
                with open(self.path, 'r') as f:
                    data = json.load(f)
                # If file is a list of names
                if isinstance(data, list):
                    self.classes = [str(x) for x in data]
                # If COCO-like categories
                elif isinstance(data, dict) and 'categories' in data:
                    cats = data.get('categories', [])
                    names = []
                    for c in cats:
                        if isinstance(c, dict) and 'name' in c:
                            names.append(str(c['name']))
                    self.classes = names
                else:
                    # Fallback: stringify top-level keys
                    self.classes = [str(x) for x in data] if isinstance(data, (list, dict)) else []
            except Exception:
                # On error, fallback to empty
                self.classes = []
        else:
            # Treat as text file: one class per line
            with open(self.path, 'r') as f:
                self.classes = [l.strip() for l in f if l.strip()]

    def get_classes(self):
        return getattr(self, 'classes', [])

    def set_classes_file(self, path):
        self.path = path
        self.load_classes()
        return self.classes

    def set_classes(self, class_list):
        self.classes = class_list

    def add_class(self, class_name):
        """Add a new class to the list if it doesn't exist."""
        if class_name and class_name not in self.classes:
            self.classes.append(class_name)

    def save_classes(self):
        """Save current classes to the file path."""
        if not self.path:
            return
        try:
            # We default to saving as TXT as it's the primary format for this file
            if self.path.lower().endswith('.json'):

                with open(self.path, 'w') as f:
                    json.dump(self.classes, f, indent=2)
            else:
                with open(self.path, 'w') as f:
                    for c in self.classes:
                        f.write(f"{c}\n")
        except Exception:
            pass

def prompt_use_discovered_json_classes(window, discovered):
    """Show a dialog listing discovered classes and allow user to rename/confirm them.
    
    Args:
        window: The main application window instance (AnnotatorMainWindow)
        discovered: Dictionary of discovered classes
    """
    # If no discovered classes, we'll still show the dialog so user can add some
    if discovered is None:
        discovered = {}

    # Create dialog with editable fields per discovered class
    dlg = QDialog(window)
    dlg.setWindowTitle("Discovered Classes - Confirm / Edit")
    dlg.setMinimumWidth(500)
    dlg.setMinimumHeight(400)

    main_layout = QVBoxLayout(dlg)
    
    # Info label
    msg = f"Found {len(discovered)} classes in annotation files." if discovered else "No classes found in annotation files."
    info = QLabel(f"{msg}\nYou can rename discovered classes or add missing ones manually.")
    main_layout.addWidget(info)
    
    # Scroll area for many classes
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll_widget = QWidget()
    form = QFormLayout(scroll_widget)
    
    edits = []
    def add_class_row(name=""):
        row_idx = len(edits)
        le = QLineEdit(name)
        le.setPlaceholderText("Enter class name...")
        label_text = f"Class {row_idx + 1}:"
        form.addRow(label_text, le)
        edits.append(le)
        # Ensure it's visible if manually added
        if name == "":
            le.setFocus()
            QTimer.singleShot(50, lambda: scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum()))

    # Initial population
    for name in sorted(discovered.keys()):
        add_class_row(name)
    
    # If none found, add one empty row to get started
    if not discovered:
        add_class_row("")

    scroll.setWidget(scroll_widget)
    main_layout.addWidget(scroll)

    # Action layout
    action_layout = QHBoxLayout()
    add_btn = QPushButton("+ Add Missing Class")
    add_btn.clicked.connect(lambda: add_class_row(""))
    action_layout.addWidget(add_btn)
    action_layout.addStretch()
    main_layout.addLayout(action_layout)
    
    # Buttons
    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.button(QDialogButtonBox.Ok).setText("Apply Classes")
    buttons.button(QDialogButtonBox.Cancel).setText("Skip (Use Current)")
    main_layout.addWidget(buttons)
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)

    if dlg.exec_() != QDialog.Accepted:
        logging.info("User chose NOT to update classes from JSON discovery.")
        return False

    # Collect edited names and ensure uniqueness
    edited = []
    seen = set()
    for le in edits:
        val = le.text().strip()
        if not val:
            continue
        
        # de-dup by appending suffix if necessary
        orig_val = val
        suffix = 1
        while val in seen:
            val = f"{orig_val}_{suffix}"
            suffix += 1
        
        seen.add(val)
        edited.append(val)

    if not edited:
        logging.warning("No classes were entered/confirmed. Keeping current classes.")
        return False

    # Apply classes for display
    window.class_manager.classes = edited
    window.canvas.classes = edited

    # Persist to disk so classes survive next launch
    try:
        import os
        classes_dir = "user_classes"
        os.makedirs(classes_dir, exist_ok=True)
        file_path = os.path.join(classes_dir, "classes.txt")
        with open(file_path, "w") as f:
            f.write("\n".join(edited))
        logging.info(f"Saved confirmed JSON classes to '{file_path}'.")
    except Exception as e:
        logging.warning(f"Could not save classes to disk: {e}")

    # Remap existing canvas boxes to the newly confirmed classes when possible
    try:
        window._remap_canvas_boxes_using_json_names()
    except Exception:
        logging.debug("_remap_canvas_boxes_using_json_names failed")

    # Refresh UI now that classes + box ids are consistent
    window.update_labels_panel(window.canvas.boxes)
    window.app_status_bar.set_status(f"Loaded {len(edited)} classes from JSON for display.")
    logging.info(f"Loaded {len(edited)} classes from JSON for display. Classes: {edited}")
    return True

def apply_discovered_json_classes(window, discovered):
    """Apply discovered classes for display without blocking the UI.

    This sets the in-memory classes used for display (class_manager + canvas)
    but does not overwrite persistent classes.txt on disk. It logs what was
    applied so the user can still change them later.
    
    Args:
        window: The main application window instance
        discovered: Dictionary or list of discovered class names
    """
    if not discovered:
        return False

    # De-duplicate and sanitize discovered names
    seen = set()
    applied = []
    for nm in discovered:
        if not nm or not isinstance(nm, str):
            continue
        s = nm.strip()
        if not s or s in seen:
            continue
        seen.add(s)
        applied.append(s)

    if not applied:
        return False
        
    # Apply classes for display
    window.class_manager.classes = applied
    window.canvas.classes = applied
    window.app_status_bar.set_status(f"Loaded {len(applied)} classes from JSON for display.")
    logging.info(f"Auto-applied {len(applied)} discovered JSON classes for display: {applied}")
    return True
