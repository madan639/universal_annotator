import logging
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget,
    QFormLayout, QLineEdit, QHBoxLayout, QPushButton,
    QDialogButtonBox
)
from PyQt5.QtCore import Qt, QTimer


def _save_classes_to_disk(classes):
    """Persist a class list to user_classes/classes.txt."""
    try:
        classes_dir = "user_classes"
        os.makedirs(classes_dir, exist_ok=True)
        file_path = os.path.join(classes_dir, "classes.txt")
        with open(file_path, "w") as f:
            f.write("\n".join(classes))
        logging.info(f"Saved {len(classes)} classes to '{file_path}': {classes}")
    except Exception as e:
        logging.warning(f"Could not save classes to disk: {e}")

def prompt_use_discovered_json_classes(window, discovered):
    """Show a dialog listing discovered classes and allow user to rename/confirm them.

    Args:
        window: The main application window instance (AnnotatorMainWindow)
        discovered: Dictionary of discovered classes
    """
    if discovered is None:
        discovered = {}

    dlg = QDialog(window)
    dlg.setWindowTitle("Discovered Classes - Confirm / Edit")
    dlg.setMinimumWidth(500)
    dlg.setMinimumHeight(400)

    main_layout = QVBoxLayout(dlg)

    msg = f"Found {len(discovered)} classes in annotation files." if discovered else "No classes found in annotation files."
    info = QLabel(f"{msg}\nYou can rename discovered classes or add missing ones manually.")
    main_layout.addWidget(info)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll_widget = QWidget()
    form = QFormLayout(scroll_widget)

    edits = []

    def add_class_row(name=""):
        row_idx = len(edits)
        le = QLineEdit(name)
        le.setPlaceholderText("Enter class name...")
        form.addRow(f"Class {row_idx + 1}:", le)
        edits.append(le)
        if name == "":
            le.setFocus()
            QTimer.singleShot(50, lambda: scroll.verticalScrollBar().setValue(
                scroll.verticalScrollBar().maximum()))

    for name in sorted(discovered.keys()):
        add_class_row(name)

    if not discovered:
        add_class_row("")

    scroll.setWidget(scroll_widget)
    main_layout.addWidget(scroll)

    action_layout = QHBoxLayout()
    add_btn = QPushButton("+ Add Missing Class")
    add_btn.clicked.connect(lambda: add_class_row(""))
    action_layout.addWidget(add_btn)
    action_layout.addStretch()
    main_layout.addLayout(action_layout)

    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.button(QDialogButtonBox.Ok).setText("Apply Classes")
    buttons.button(QDialogButtonBox.Cancel).setText("Skip (Use Current)")
    main_layout.addWidget(buttons)
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)

    if dlg.exec_() != QDialog.Accepted:
        logging.info("User chose NOT to update classes from JSON discovery.")
        # Still save the current in-memory classes so they persist to disk
        current = window.class_manager.get_classes()
        if current:
            _save_classes_to_disk(current)
        return False

    edited = []
    seen = set()
    for le in edits:
        val = le.text().strip()
        if not val:
            continue
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

    window.class_manager.classes = edited
    window.canvas.classes = edited

    # Persist to disk so classes survive next launch
    _save_classes_to_disk(edited)

    try:
        window._remap_canvas_boxes_using_json_names()
    except Exception:
        logging.debug("_remap_canvas_boxes_using_json_names failed")

    window.update_labels_panel(window.canvas.boxes)
    window.app_status_bar.set_status(f"Loaded {len(edited)} classes from JSON for display.")
    logging.info(f"Loaded {len(edited)} classes from JSON for display. Classes: {edited}")
    return True


def apply_discovered_json_classes(window, discovered):
    """Apply discovered classes silently without a dialog."""
    if not discovered:
        return False

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

    window.class_manager.classes = applied
    window.canvas.classes = applied
    _save_classes_to_disk(applied)
    window.app_status_bar.set_status(f"Loaded {len(applied)} classes from JSON for display.")
    logging.info(f"Auto-applied {len(applied)} discovered JSON classes: {applied}")
    return True
