import os
import json
import logging
import re
from PyQt5.QtWidgets import ( 
    QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QFileDialog, QApplication,
    QMessageBox, QCheckBox, QSizePolicy, QListWidgetItem, QDialog, QLabel,
    QTextEdit, QPushButton, QProgressDialog, QFormLayout, QLineEdit, QDialogButtonBox, QLabel, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt, QTimer
from .canvas_widget import CanvasWidget
from .class_manager import ClassManager
from .managers import ImageManager, AnnotationManager, FormatManager, AutoSaveManager
from .json_helper import JSONHelper
from ui.themes import ThemeManager 
from ui.components import LabelPanel, ControlPanel, LabelListItemWidget
from ui.dialogs import ClassSelectionDialog, HelpDialog, AboutDialog, ClassManagementDialog 
from ui.menus import AppMenuBar
from ui.statusbar import AppStatusBar
from ui.messages import get_tooltip, get_status_message
from ui.mode_panel import ModePanel
from core.enums import AppMode, DrawingTool
from converters.txt_to_json_converter import convert_txt_to_json
from converters.json_to_txt import convert_json_to_txt
from converters.txt_to_annotaion_coco_json import convert_txt_to_coco
from converters.json_to_coco_merge import convert_json_folder_to_coco
from converters.coco_to_json_converter import convert_coco_to_json_folder
from converters.coco_to_txt_converter import convert_coco_to_txt
from exporters.json_exporter import save_json
from exporters.coco_exporter import save_coco
from utils.file_utils import list_images
from core.loaders import load_txt_annotations, load_json_annotations, load_coco_annotations
from PIL import Image
import traceback


def natural_sort_key(filename):
    """Convert a string into a list of mixed integers and strings for natural sorting.
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', filename)]


class AnnotatorMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal Annotator Tool")
        self.setGeometry(100, 100, 1600, 900)
        
        # --- Theme ---
        self.setStyleSheet("""
            QWidget {
                background-color: #2e2e2e;
                color: #e0e0e0;
                font-family: "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
                font-size: 10pt;
            }
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #5a5a5a;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5a5a5a; }
        """)

        # --- Managers & Helpers ---
        self.image_manager = ImageManager()
        self.annotation_manager = AnnotationManager()
        self.format_manager = FormatManager()
        self.autosave_manager = AutoSaveManager(save_callback=self.save_annotation)
        self.json_helper = JSONHelper()
        
        # --- State ---
        self.mode = "view"
        self.format = "TXT"  # Default format
        self.annotation_mode = "annotation"  # "annotation" for boxes, "segmentation" for polygons
        self.class_manager = ClassManager(os.path.join(os.getcwd(), "sample_classes", "classes.txt"))
        
        # JSON-specific state
        self.json_name_keys = ['className', 'category_name', 'name', 'label']
        self.json_bbox_methods = ['contour', 'bbox', 'points', 'xywh']
        self.json_display_override = False
        self._cached_json_structure = None
        self.detected_classes = []
        
        # Convenience aliases for backward compatibility during transition
        # These will be gradually phased out
        self.image_dir = None
        self.label_dir = None
        self.coco_file_path = None
        self.image_files = []
        self.current_index = 0
        self.selected_box_indices = set()
        self.image_selections = {}
        self.manual_deselect_all = False

        # --- Status Bar (must be created before canvas to connect signals) ---
        self.app_status_bar = AppStatusBar(self)
        self.setStatusBar(self.app_status_bar)

        # --- Canvas ---
        self.canvas = CanvasWidget(self, mode=self.mode, classes=self.class_manager.get_classes())
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.box_added.connect(self.on_box_added)  # Connect to box added signal
        self.canvas.polygon_added.connect(self.on_polygon_added) # Connect to polygon added signal
        self.canvas.box_clicked_on_canvas.connect(self.on_canvas_box_clicked) # Connect canvas box click signal
        self.canvas.drawing_cancelled.connect(self.on_drawing_cancelled) # Connect drawing cancellation
        self.canvas.zoom_changed.connect(self.app_status_bar.set_zoom_level) # Connect zoom signal

        # --- Labels Panel (Right Side) ---
        self.labels_panel = LabelPanel()
        self.labels_list = self.labels_panel.labels_list
        self.select_all_btn = self.labels_panel.select_all_btn
        self.deselect_all_btn = self.labels_panel.deselect_all_btn
        self.delete_selected_btn = self.labels_panel.delete_selected_btn

        # --- Control Panel (Left Side) ---
        self.control_panel = ControlPanel()
        self.load_btn = self.control_panel.load_btn
        self.format_btn = self.control_panel.format_btn
        self.load_classes_btn = self.control_panel.load_classes_btn
        self.mode_edit_btn = self.control_panel.mode_edit_btn
        self.mode_view_btn = self.control_panel.mode_view_btn
        self.prev_btn = self.control_panel.prev_btn
        self.next_btn = self.control_panel.next_btn
        self.save_btn = self.control_panel.save_btn
        self.convert_to_json_btn = self.control_panel.convert_to_json_btn
        self.convert_to_txt_btn = self.control_panel.convert_to_txt_btn
        self.current_format_display = self.control_panel.current_format_label
        self.convert_to_coco_btn = self.control_panel.convert_to_coco_btn
        self.merge_json_btn = self.control_panel.merge_json_btn 
        self.convert_coco_to_json_btn = self.control_panel.convert_coco_to_json_btn
        self.convert_coco_to_txt_btn = self.control_panel.convert_coco_to_txt_btn
        self.image_jump_box = self.control_panel.image_jump_box
        self.auto_save_cb = QCheckBox("Auto Save")
        
        # Add auto_save_cb to control panel
        self.control_panel.auto_save_cb = self.auto_save_cb

        # Add Auto Save checkbox to the control panel layout
        # self.control_panel.layout().insertWidget(self.control_panel.layout().count() - 1, self.auto_save_cb)
        
        # --- NEW: Mode Panel (Annotation vs Segmentation) ---
        self.mode_panel = ModePanel(self)
        # Connect signals
        self.mode_panel.mode_changed.connect(self._on_app_mode_changed)
        self.mode_panel.tool_changed.connect(self._on_drawing_tool_changed)
        
        # --- Status Label ---
        self.status_label = QLabel("View Mode (Read Only)")
        self.status_label.setStyleSheet("padding: 8px; font-weight: bold;")

        # --- Layout ---
        # Left sidebar: Controls
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.control_panel)
        left_layout.addWidget(self.mode_panel) # Explicitly add here
        left_layout.addWidget(self.auto_save_cb) # Explicitly add here
        left_layout.addStretch()
        left_panel = QWidget()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(280)

        # Main content: Canvas + Labels
        content_layout = QHBoxLayout()
        content_layout.addWidget(self.canvas, stretch=1)
        content_layout.addWidget(self.labels_panel, stretch=0)
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(left_panel, stretch=0)
        main_layout.addLayout(content_layout, stretch=1)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Full layout with status
        full_layout = QVBoxLayout()
        full_layout.addLayout(main_layout, stretch=1)
        full_layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(full_layout)
        self.setCentralWidget(container)

        # --- Menu Bar ---
        self.menu_bar = AppMenuBar(self)
        self.setMenuBar(self.menu_bar)

        # --- Connections ---
        self.load_btn.clicked.connect(self.load_dataset)
        self.format_btn.clicked.connect(self.select_format)
        self.mode_edit_btn.clicked.connect(self.set_edit_mode)
        self.mode_view_btn.clicked.connect(self.set_view_mode)
        self.prev_btn.clicked.connect(self.prev_image)
        self.next_btn.clicked.connect(self.next_image)
        self.save_btn.clicked.connect(self.save_annotation)
        self.load_classes_btn.clicked.connect(self.load_classes_file)
        self.labels_list.itemChanged.connect(self.on_label_toggled)
        self.labels_list.itemClicked.connect(self.on_label_clicked)
        self._connect_signals()

        # Check classes on startup
        QTimer.singleShot(0, self.check_classes_file)

    def on_label_clicked(self, item):
        """Handle clicking a label in the list to select it on canvas."""
        idx = item.data(Qt.UserRole)
        if idx is not None:
             # Find widget and toggle
             widget = self.labels_list.itemWidget(item)
             if widget:
                 widget.toggle_selection() 
             # Also ensure it's selected directly
             self.selected_box_indices = {idx}
             self.canvas.selected_boxes = self.selected_box_indices
             self.canvas.update()
             # Update list visuals
             self._update_list_selection_visuals()

    def _update_list_selection_visuals(self):
        """Update checkboxes in the labels list to match selected_box_indices."""
        self.labels_list.blockSignals(True)
        for i in range(self.labels_list.count()):
            item = self.labels_list.item(i)
            box_idx = item.data(Qt.UserRole)
            widget = self.labels_list.itemWidget(item)
            
            if widget and hasattr(widget, 'checkbox'):
                should_be_checked = box_idx in self.selected_box_indices
                widget.checkbox.blockSignals(True)
                widget.checkbox.setChecked(should_be_checked)
                widget.checkbox.blockSignals(False)
        self.labels_list.blockSignals(False)

    def _connect_signals(self):
        """Connect remaining signals"""
        self.select_all_btn.clicked.connect(self.select_all_labels)
        self.delete_selected_btn.clicked.connect(self.delete_selected_boxes)
        self.deselect_all_btn.clicked.connect(self.deselect_all_labels)
        self.convert_to_json_btn.clicked.connect(self.convert_annotations_to_json)
        self.convert_to_txt_btn.clicked.connect(self.convert_annotations_to_txt)
        self.convert_to_coco_btn.clicked.connect(self.convert_annotations_to_coco)
        self.merge_json_btn.clicked.connect(self.merge_json_to_coco_json)
        self.convert_coco_to_json_btn.clicked.connect(self.convert_coco_to_per_image_json)
        self.convert_coco_to_txt_btn.clicked.connect(self.convert_coco_to_txt)
        self.image_jump_box.currentIndexChanged.connect(self.on_jump_box_activated)

        # Start in view mode
        self.set_view_mode()
        
        self._update_format_display()

        # Set focus to the main window to capture key presses
        self.setFocusPolicy(Qt.StrongFocus)

        # --- Add Tooltips ---
        self._setup_tooltips()
        
        # Initialize Shortcuts
        self.init_shortcuts()

    def check_classes_file(self):
        """Check if classes file exists, if not prompt user."""
        if not os.path.exists(self.class_manager.path):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Classes File Not Found")
            msg.setText("Default classes file not found.\nWhat would you like to do?")
            create_btn = msg.addButton("Create New / Use Default", QMessageBox.AcceptRole)
            load_btn = msg.addButton("Select Existing File", QMessageBox.ActionRole)
            msg.addButton(QMessageBox.Cancel)
             
            msg.exec_()
             
            if msg.clickedButton() == load_btn:
                self.load_classes_file()
            elif msg.clickedButton() == create_btn:
                # Open class management dialog to let them create/edit
                dialog = ClassManagementDialog(self.class_manager, self)
                dialog.exec_()

    # ----------------------------------------------------------------
    def _setup_tooltips(self):
        """Setup tooltips for all UI elements"""
        self.load_btn.setToolTip(get_tooltip("load_dataset"))
        self.load_classes_btn.setToolTip("Load a classes.txt or classes.json file to populate class labels")
        self.format_btn.setToolTip(get_tooltip("format_btn"))
        self.mode_edit_btn.setToolTip(get_tooltip("edit_mode"))
        self.mode_view_btn.setToolTip(get_tooltip("view_mode"))
        self.prev_btn.setToolTip(get_tooltip("prev_btn"))
        self.next_btn.setToolTip(get_tooltip("next_btn"))
        self.save_btn.setToolTip(get_tooltip("save_btn"))
        self.select_all_btn.setToolTip(get_tooltip("select_all_btn"))
        self.deselect_all_btn.setToolTip(get_tooltip("deselect_all_btn"))
        self.delete_selected_btn.setToolTip("Delete all currently selected boxes (Delete Key)")
        self.auto_save_cb.setToolTip(get_tooltip("auto_save_cb"))
        self.convert_to_json_btn.setToolTip("Convert annotations from TXT to JSON format")
        self.convert_to_txt_btn.setToolTip("Convert annotations from JSON to TXT format")
        self.convert_to_coco_btn.setToolTip("Convert TXT annotations to a single COCO JSON file")
        self.merge_json_btn.setToolTip("Merge a folder of individual JSON files into a single COCO JSON file")
        self.convert_coco_to_json_btn.setToolTip("Convert a single COCO JSON file into multiple per-image JSON files")
        self.convert_coco_to_txt_btn.setToolTip("Convert a single COCO JSON file into multiple txt .txt files")
        self.image_jump_box.setToolTip("Jump to a specific image in the dataset")
    
    def show_help(self):
        """Show help dialog"""
        help_dialog = HelpDialog(self)
        help_dialog.exec_()
    
    def show_about(self):
        """Show about dialog"""
        about_dialog = AboutDialog(self)
        about_dialog.exec_()

    def on_drawing_cancelled(self):
        """Handles the signal from the canvas when drawing is cancelled."""
        self.app_status_bar.set_status("Box creation cancelled.")
        logging.info("User cancelled drawing a box via Esc key.")

    def on_canvas_box_clicked(self, clicked_box_idx):
        """
        Handles a click on a bounding box directly on the canvas.
        Selects only the clicked box and updates the UI.
        """
        logging.debug(f"Canvas box {clicked_box_idx} clicked. Current selections: {self.selected_box_indices}")
        
        # Set the selection to ONLY the clicked box.
        # This ensures that even if other boxes were selected, the click action
        # focuses on just the one under the cursor.
        self.selected_box_indices = {clicked_box_idx} 
        self.update_labels_panel(self.canvas.boxes) # Refresh UI to show only this one selected
        self.image_selections[self.current_index] = self.selected_box_indices.copy()

    def on_jump_box_activated(self, index):
        """Jumps to the image selected in the image_jump_box dropdown."""
        # The signal is emitted even when we programmatically change the index,
        # so we check if the index is actually different from the current one.
        if index == self.current_index or index == -1:
            return

        logging.info(f"User jumped to image {index + 1} via dropdown.")

        # Save current state before jumping
        if self.canvas.changed:
            self.prompt_save_changes()
        self.image_selections[self.current_index] = self.selected_box_indices.copy()

        self.current_index = index
        self.load_image()

    def delete_specific_box(self, box_idx_to_delete):
        """
        Deletes a specific bounding box by its index.
        This is called by the individual delete buttons in the labels panel.
        """
        if self.mode != "edit":
            if self.prompt_switch_to_edit_mode():
                self.set_edit_mode()
            return

        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete box #{box_idx_to_delete}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.No:
            self.app_status_bar.set_status("Deletion cancelled.")
            return

        img_name = self.image_files[self.current_index] if self.image_files else "<no-image>"
        logging.info(f"Image '{img_name}': Deleting specific box with index: {box_idx_to_delete}")

        # Remove the box from the canvas list
        if 0 <= box_idx_to_delete < len(self.canvas.boxes):
            self.canvas.boxes.pop(box_idx_to_delete)
            self.canvas.changed = True

        # Re-index selected boxes and update UI
        self._reindex_selections_after_deletion(box_idx_to_delete)
        self.update_labels_panel(self.canvas.boxes)
        self.save_annotation(auto=True)
        self.app_status_bar.set_status(f"Deleted box #{box_idx_to_delete}.")
    
    def _on_app_mode_changed(self, mode):
        """Handle switch between Detection and Segmentation."""
        logging.info(f"App Mode changed to: {mode}")
        if mode == AppMode.SEGMENTATION:
             self.annotation_mode = "segmentation"
             status = "Segmentation Mode: Draw Polygons"
        else:
             self.annotation_mode = "annotation"
             status = "Detection Mode: Draw Boxes or Polygons"
        self.app_status_bar.set_status(status)
        # Reload current image with new mode filter
        if self.image_files:
            self.load_image()

    def _on_drawing_tool_changed(self, tool):
        """Update canvas tool."""
        self.canvas.current_tool = tool
        logging.info(f"Drawing Tool changed to: {tool}")
        if tool == DrawingTool.POLYGON:
            get_status_message("Polygon Mode: Click to add points, Enter to finish")

    def delete_selected_boxes(self):
        """Delete all currently selected bounding boxes."""
        if self.mode != "edit":
            if self.prompt_switch_to_edit_mode():
                self.set_edit_mode() # Ensure mode is updated if user agreed
            return
        num_selected = len(self.selected_box_indices)
        
        if num_selected == 0:
            self.app_status_bar.set_status("No boxes selected to delete.")
            return

        # --- Add confirmation for multiple deletions ---
        if num_selected > 1:
            reply = QMessageBox.question(
                self, "Confirm Deletion",
                f"Are you sure you want to delete {num_selected} selected boxes?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                self.app_status_bar.set_status("Deletion cancelled.")
                return

        img_name = self.image_files[self.current_index] if self.image_files else "<no-image>"
        
        # Delete in descending order to keep indices valid during valid
        # We need to handle boxes and polygons separately but process indices carefully
        
        # Sort indices descending
        sorted_indices = sorted(list(self.selected_box_indices), reverse=True)
        
        boxes_len = len(self.canvas.boxes)
        
        for idx in sorted_indices:
            if idx >= boxes_len:
                # It's a polygon
                p_idx = idx - boxes_len
                if 0 <= p_idx < len(self.canvas.polygons):
                    self.canvas.polygons.pop(p_idx)
            else:
                # It's a box
                if 0 <= idx < len(self.canvas.boxes):
                    self.canvas.boxes.pop(idx)
        
        # Reset selection
        self.selected_box_indices = set()
        self.canvas.selected_boxes = set()
        self.image_selections[self.current_index] = set()
        
        self.canvas.changed = True
        self.canvas.update()
        self.update_labels_panel(self.canvas.boxes) # Refresh list
        
        self.app_status_bar.set_status(f"Deleted {num_selected} items.")
        logging.info(f"Deleted {num_selected} items (boxes/polygons).")
        # Persist the new selection state for the current image.
        # After deleting, we default to selecting all remaining boxes.
        self.image_selections[self.current_index] = self.selected_box_indices.copy()

        # --- UI Refresh ---
        self.update_labels_panel(self.canvas.boxes)

        # --- Save and Finalize ---
        self.save_annotation(auto=True)
        self.update_status_label()
        self.app_status_bar.set_status(f"Deleted {len(indices_to_delete)} selected boxes.")

    def _reindex_selections_after_deletion(self, deleted_idx):
        """Adjusts selected_box_indices and image_selections after a single box deletion."""
        new_selected = set()
        for idx in self.selected_box_indices:
            if idx < deleted_idx:
                new_selected.add(idx)
            elif idx > deleted_idx:
                new_selected.add(idx - 1)
        self.selected_box_indices = new_selected
        self.image_selections[self.current_index] = self.selected_box_indices.copy()

    def _reindex_selections_after_multiple_deletions(self, deleted_indices):
        """Adjusts selected_box_indices and image_selections after multiple box deletions."""
        # Convert to a sorted list of indices to delete
        deleted_indices_sorted = sorted(list(deleted_indices))
        
        new_selected = set()
        for old_idx in self.selected_box_indices:
            # Calculate how many boxes before old_idx were deleted
            shift = sum(1 for d_idx in deleted_indices_sorted if d_idx < old_idx)
            new_idx = old_idx - shift
            
            # Only add if the box wasn't one of the deleted ones
            if old_idx not in deleted_indices:
                new_selected.add(new_idx)
        
        self.selected_box_indices = new_selected
        self.image_selections[self.current_index] = self.selected_box_indices.copy()

    def load_classes_file(self):
        """Allow user to pick a classes file (txt or json) and reload classes."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Class File", os.getcwd(), "JSON Files (*.json);;Text Files (*.txt);;All Files (*)")
        if not file_path:
            return
        
        if file_path.lower().endswith('.txt'):
            self.class_manager.set_classes_file(file_path)
            self.canvas.classes = self.class_manager.get_classes()
            self._show_loaded_classes_dialog()
            # Refresh labels panel to show correct class names for current annotations
            if self.canvas.boxes:
                self.update_labels_panel(self.canvas.boxes)
                self.canvas.update()
            return

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, dict) or 'categories' not in data:
                msg = "The selected JSON file does not contain a 'categories' list."
                QMessageBox.warning(self, "Invalid Format", msg)
                logging.warning(f"Invalid classes JSON: {msg}")
                return

            categories = data.get('categories', [])
            extracted_classes = [cat.get('name', 'Unnamed') for cat in categories if isinstance(cat, dict)]

            if not extracted_classes:
                msg = "No class names could be extracted from the 'categories' list."
                QMessageBox.warning(self, "No Classes Found", msg)
                logging.warning(f"No classes found in JSON: {msg}")
                return

            # Show confirmation dialog
            class_list_str = "\n".join([f"- {name}" for name in extracted_classes[:15]])
            if len(extracted_classes) > 15:
                class_list_str += "\n- ..."

            reply = QMessageBox.question(self, "Confirm Classes", f"Found the following classes:\n\n{class_list_str}\n\nIs this correct?", QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                # Apply classes in the order provided by the COCO categories list
                self.class_manager.classes = extracted_classes
                self.canvas.classes = extracted_classes

                # Persist mapping from COCO category id -> category name and -> local index
                try:
                    coco_map = {}
                    coco_id_to_index = {}
                    for idx, cat in enumerate(categories):
                        if isinstance(cat, dict):
                            cid = cat.get('id') or cat.get('category_id')
                            name = cat.get('name') or cat.get('label') or extracted_classes[idx]
                            if cid is not None:
                                try:
                                    coco_map[int(cid)] = name
                                    coco_id_to_index[int(cid)] = idx
                                except Exception:
                                    pass
                    setattr(self, 'json_coco_category_map', coco_map)
                    setattr(self, 'json_coco_id_to_index', coco_id_to_index)
                except Exception:
                    pass

                # Refresh UI and mappings
                self.update_labels_panel(self.canvas.boxes)
                self.canvas.update()
                self.app_status_bar.set_status(f"Loaded {len(extracted_classes)} classes from JSON.")
                logging.info(f"Loaded {len(extracted_classes)} classes from '{file_path}'.")
                return True
            return False
        except Exception as e:
            msg = f"An error occurred while reading the JSON file:\n{str(e)}"
            QMessageBox.critical(self, "Error Loading File", msg)
            logging.error(f"Failed to load classes from JSON: {e}")
            return False
    
    def _confirm_and_load_classes_from_json(self, file_path):
        """Reads a JSON file, asks user to confirm classes, and loads them."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, dict) or 'categories' not in data:
                msg = "The selected JSON file does not contain a 'categories' list."
                QMessageBox.warning(self, "Invalid Format", msg)
                logging.warning(f"Invalid COCO for classes: {msg}")
                return False

            categories = data.get('categories', [])
            extracted_classes = [cat.get('name', 'Unnamed') for cat in categories if isinstance(cat, dict)]

            if not extracted_classes:
                msg = "No class names could be extracted from the 'categories' list."
                QMessageBox.warning(self, "No Classes Found", msg)
                logging.warning(f"No classes found in COCO file: {msg}")
                return False

            class_list_str = "\n".join([f"- {name}" for name in extracted_classes[:15]])
            if len(extracted_classes) > 15:
                class_list_str += "\n- ..."

            reply = QMessageBox.question(self, "Confirm Classes", f"Found the following classes:\n\n{class_list_str}\n\nIs this correct?", QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.class_manager.classes = extracted_classes
                self.canvas.classes = extracted_classes
                self.update_labels_panel(self.canvas.boxes)
                self.app_status_bar.set_status(f"Loaded {len(extracted_classes)} classes from JSON.")
                logging.info(f"Confirmed and loaded {len(extracted_classes)} classes from '{file_path}'.")
                return True
            else:
                logging.info("User rejected the extracted classes.")
                return False  # User cancelled
        except Exception as e:
            msg = f"An error occurred while reading the JSON file:\n{str(e)}"
            QMessageBox.critical(self, "Error Loading File", msg)
            logging.error(f"Failed to read classes from COCO JSON: {e}")
            return False

    def _show_loaded_classes_dialog(self):
        """Show a dialog displaying the loaded classes from classes.txt file with option to change them."""
        classes = self.class_manager.get_classes()
        
        if not classes:
            return
        
        # Create the message with class list
        class_list_str = "\n".join([f"{i}. {name}" for i, name in enumerate(classes[:20])])
        if len(classes) > 20:
            class_list_str += f"\n... and {len(classes) - 20} more classes"
        
        msg = f"Classes loaded from classes.txt file:\n\n{class_list_str}\n\n" \
              f"Total classes: {len(classes)}\n\n" \
              f"If you want to change these classes, click 'Load Different Classes' button above."
        
        QMessageBox.information(
            self,
            "Classes Loaded Successfully",
            msg
        )
        
        logging.info(f"Displayed loaded classes dialog. Total classes: {len(classes)}")

    def refresh_image(self):
        """Reload current image"""
        if self.image_files:
            self.load_image()
            self.app_status_bar.set_status("Image refreshed")
    
    def toggle_auto_save(self):
        """Toggle auto-save checkbox"""
        self.auto_save_cb.setChecked(not self.auto_save_cb.isChecked())

    def prompt_switch_to_edit_mode(self):
        """
        Prompts the user to switch to Edit Mode.
        Returns True if user agrees, False otherwise.
        """
        reply = QMessageBox.question(
            self, "Switch to Edit Mode?",
            "You are in View Mode. Do you want to switch to Edit Mode to perform this action?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.set_edit_mode()
            return True
        return False

    # ----------------------------------------------------------------
    def reload_data_for_new_format(self):
        """When user changes format, let them select images and decide on labels."""
        logging.info(f"Format changed to {self.format}.")
        
        # For COCO, use different workflow
        if self.format == "COCO":
            self._reload_data_for_coco()
            return
        
        # For TXT and JSON
        # Ask user to select image folder
        img_dir = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if not img_dir:
            logging.info("Format change cancelled - no image folder selected")
            return
        
        # Get image files
        image_files = list_images(img_dir)
        if not image_files:
            QMessageBox.warning(self, "No Images", "No image files found in the selected folder.")
            logging.warning(f"No images found in: {img_dir}")
            return
        
        image_files = sorted(image_files, key=natural_sort_key)
        
        # Ask: Create new label files OR use existing
        reply = QMessageBox.question(
            self, "Label Files",
            f"Do you want to:\n\n"
            f"YES: Create new label files in {self.format} format\n"
            f"NO: Use existing label files",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Create new label files
            img_parent = os.path.dirname(img_dir.rstrip('/\\'))
            suggested_lbl_dir = os.path.join(img_parent, 'labels')
            
            # Check if labels folder exists
            if os.path.isdir(suggested_lbl_dir):
                warn_reply = QMessageBox.warning(
                    self, "Labels Folder Exists",
                    f"Labels folder already exists at:\n{suggested_lbl_dir}\n\n"
                    f"This will create new files and may overwrite existing ones.\n\n"
                    f"Continue?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if warn_reply == QMessageBox.No:
                    return
            
            try:
                os.makedirs(suggested_lbl_dir, exist_ok=True)
                lbl_dir = suggested_lbl_dir
                logging.info(f"Created labels folder: {lbl_dir}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to create labels folder:\n{str(e)}")
                logging.error(f"Failed to create labels folder: {e}")
                return
            
            # Set and create files
            self.image_dir = img_dir
            self.label_dir = lbl_dir
            self.image_files = image_files
            self.current_index = 0
            self.selected_box_indices = set()
            self.manual_deselect_all = False  # Reset for new format
            self.image_selections = {}
            
            self._create_initial_files()
            self._populate_image_jump_box()  # Populate jump box for new dataset
            self.load_image()
            self.app_status_bar.set_status(f"Dataset loaded with {self.format} format.")
            logging.info(f"Dataset loaded with {self.format} format. Images: {len(image_files)}")
        
        else:
            # Use existing label files
            lbl_dir = QFileDialog.getExistingDirectory(self, "Select Label Folder")
            if not lbl_dir:
                logging.info("Label folder selection cancelled")
                return
            
            # Check if label files exist for this format
            label_files_exist = False
            if os.path.isdir(lbl_dir):
                try:
                    files = os.listdir(lbl_dir)
                    if self.format == "TXT":
                        label_files_exist = any(f.endswith('.txt') for f in files)
                    elif self.format == "JSON":
                        label_files_exist = any(f.endswith('.json') for f in files)
                except Exception:
                    pass
            
            if not label_files_exist:
                QMessageBox.warning(
                    self, "No Labels Found",
                    f"No {self.format} label files found in:\n{lbl_dir}\n\n"
                    f"Please select a folder with {self.format} files or create new ones."
                )
                logging.warning(f"No {self.format} files found in: {lbl_dir}")
                return
            
            # Set and load
            self.image_dir = img_dir
            self.label_dir = lbl_dir
            self.image_files = image_files
            self.current_index = 0
            self.selected_box_indices = set()
            self.manual_deselect_all = False
            self.image_selections = {}
            
            # Trigger class discovery for JSON format
            if self.format == 'JSON':
                logging.info("[RELOAD] JSON format detected, triggering class discovery...")
                self._handle_json_class_discovery()
            
            self._populate_image_jump_box()
            self.load_image()
            self.app_status_bar.set_status(f"Dataset loaded with {self.format} format.")
            logging.info(f"Dataset loaded with {self.format} format. Images: {len(image_files)}")

    def _reload_data_for_coco(self):
        """Special workflow for COCO format: select image folder and COCO file."""
        logging.info("COCO format: Starting workflow...")
        
        # Step 1: Select image folder
        img_dir = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if not img_dir:
            logging.info("COCO workflow cancelled - no image folder selected")
            return
        
        # Get image files
        image_files = list_images(img_dir)
        if not image_files:
            QMessageBox.warning(self, "No Images", "No image files found in the selected folder.")
            logging.warning(f"No images found in: {img_dir}")
            return
        
        image_files = sorted(image_files, key=natural_sort_key)
        
        # Step 2: Ask - Create new COCO file or use existing
        reply = QMessageBox.question(
            self, "COCO Annotation File",
            f"Do you want to:\n\n"
            f"YES: Create new COCO annotation file\n"
            f"NO: Use existing COCO annotation file",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Create new COCO file in same parent as images
            img_parent = os.path.dirname(img_dir.rstrip('/\\'))
            coco_file_path = os.path.join(img_parent, '_annotations.coco.json')
            
            # Check if file exists
            if os.path.isfile(coco_file_path):
                warn_reply = QMessageBox.warning(
                    self, "COCO File Exists",
                    f"COCO file already exists at:\n{coco_file_path}\n\n"
                    f"This will create a new file and overwrite existing annotations.\n\n"
                    f"Continue?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if warn_reply == QMessageBox.No:
                    return
            
            # Create COCO structure with images
            coco_data = {
                "info": {"description": "COCO dataset created by Universal Annotator"},
                "licenses": [],
                "images": [],
                "annotations": [],
                "categories": []
            }
            
            # Add image entries
            for idx, img_file in enumerate(image_files):
                img_path = os.path.join(img_dir, img_file)
                try:
                    img = Image.open(img_path)
                    width, height = img.size
                except Exception:
                    width, height = 0, 0
                
                coco_data["images"].append({
                    "id": idx + 1,
                    "file_name": img_file,
                    "width": width,
                    "height": height
                })
            
            # Save COCO file
            try:
                with open(coco_file_path, 'w') as f:
                    json.dump(coco_data, f, indent=2)
                logging.info(f"Created COCO file: {coco_file_path}")
                QMessageBox.information(
                    self, "COCO File Created",
                    f"Created COCO annotation file:\n{coco_file_path}\n\n"
                    f"Ready to annotate {len(image_files)} images."
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to create COCO file:\n{str(e)}")
                logging.error(f"Failed to create COCO file: {e}")
                return
            
            # Set paths and load
            self.image_dir = img_dir
            self.label_dir = img_parent
            self.image_files = image_files
            self.current_index = 0
            self.selected_box_indices = set()
            self.manual_deselect_all = False
            self.image_selections = {}
            self.coco_file_path = coco_file_path
            
            self._populate_image_jump_box()  # Populate jump box for new COCO dataset
            self.load_image()
            self.app_status_bar.set_status(f"Dataset loaded with COCO format.")
            logging.info(f"Dataset loaded with COCO format. Images: {len(image_files)}. COCO file: {coco_file_path}")
        
        else:
            # Use existing COCO file
            coco_path, _ = QFileDialog.getOpenFileName(
                self, "Select COCO Annotation File", os.getcwd(), "COCO JSON (*.json);;All Files (*)"
            )
            if not coco_path:
                logging.info("COCO file selection cancelled")
                return
            
            # Validate COCO file
            try:
                with open(coco_path, 'r') as f:
                    coco_data = json.load(f)
                
                if not isinstance(coco_data, dict) or 'images' not in coco_data:
                    QMessageBox.warning(self, "Invalid COCO File", "Selected file is not a valid COCO format file.")
                    logging.warning(f"Invalid COCO file: {coco_path}")
                    return
                
                logging.info(f"Validated COCO file with {len(coco_data.get('images', []))} images")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to read COCO file:\n{str(e)}")
                logging.error(f"Failed to read COCO file: {e}")
                return
            
            # Set paths and load
            self.image_dir = img_dir
            self.label_dir = os.path.dirname(coco_path)
            self.image_files = image_files
            self.current_index = 0
            self.selected_box_indices = set()
            self.manual_deselect_all = False  # Reset for new format
            self.image_selections = {}
            self.coco_file_path = coco_path
            
            self._populate_image_jump_box()  # Populate jump box for existing COCO dataset
            self.load_image()
            self.app_status_bar.set_status(f"Dataset loaded with COCO format.")
            logging.info(f"Dataset loaded with COCO format. Images: {len(image_files)}. COCO file: {coco_path}")



    def load_dataset(self, prefer_format=None):
        # ---------------------------------------------------------
        # HARD RESET OF ALL JSON + CLASS DETECTION STATE
        # ---------------------------------------------------------
        self.json_name_keys = []
        self.json_bbox_methods = []
        self._cached_json_structure = None
        self.detected_classes = []
        self.coco_file_path = None
        self.json_display_override = False

        # Load classes respecting precedence
        try:
            current = self.class_manager.get_classes() or []
            if current:
                logging.info("Using in-memory classes (preserve manual/session classes)")
            else:
                # Try user_classes first
                user_path = os.path.join(os.getcwd(), 'user_classes', 'classes.txt')
                sample_path = os.path.join(os.getcwd(), 'sample_classes', 'classes.txt')
                if os.path.exists(user_path):
                    try:
                        self.class_manager.set_classes_file(user_path)
                        logging.info(f"Loaded classes from user_classes: {user_path}")
                    except Exception:
                        logging.debug("Failed to load user_classes/classes.txt")
                elif os.path.exists(sample_path):
                    try:
                        self.class_manager.set_classes_file(sample_path)
                        logging.info(f"Loaded classes from sample_classes: {sample_path}")
                    except Exception:
                        logging.debug("Failed to load sample_classes/classes.txt")
                else:
                    if not hasattr(self.class_manager, 'classes'):
                        self.class_manager.classes = []
        except Exception:
            self.class_manager.classes = []

        # Reset mapping caches
        if hasattr(self, "class_map"):
            self.class_map = {}
        if hasattr(self, "normalized_map"):
            self.normalized_map = {}

        logging.info("<-> State reset before loading dataset.")
        img_dir = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if not img_dir:
            return
        
        # Suggest labels folder
        img_parent = os.path.dirname(img_dir.rstrip('/\\'))
        suggested_lbl_dir = os.path.join(img_parent, 'labels')
        folder_exists = os.path.isdir(suggested_lbl_dir)
        
        # Ask user: Create new or select existing
        if folder_exists:
            msg = f"Labels folder already exists at: {suggested_lbl_dir}\n\nUse it?"
        else:
            msg = f"Create new labels folder at: {suggested_lbl_dir}?"
        
        reply = QMessageBox.question(self, "Labels Folder", msg, QMessageBox.Yes | QMessageBox.No)
        
        created_new_folder = False
        if reply == QMessageBox.Yes:
            if not folder_exists:
                try:
                    os.makedirs(suggested_lbl_dir, exist_ok=True)
                    created_new_folder = True
                    logging.info(f"Created labels folder: {suggested_lbl_dir}")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to create folder:\n{str(e)}")
                    return
            lbl_dir = suggested_lbl_dir
        else:
            lbl_dir = QFileDialog.getExistingDirectory(self, "Select Label Folder")
            if not lbl_dir:
                return

        # Use ImageManager to load dataset
        if not self.image_manager.load_dataset(img_dir):
            QMessageBox.warning(self, "No Images", "No image files found.")
            self.app_status_bar.set_status(get_status_message("no_images"))
            return
        
        # Sync backward compatibility aliases
        self.image_dir = img_dir
        self.label_dir = lbl_dir
        self.image_files = self.image_manager.image_files
        self.current_index = 0
        
        # Set label directory in FormatManager
        self.format_manager.set_label_directory(lbl_dir)

        # Determine format
        if created_new_folder:
            self.format = "TXT"
            self.format_manager.set_format("TXT")
            self._create_initial_files()
        else:
            if prefer_format:
                self.format = prefer_format
                self.format_manager.set_format(prefer_format)
            else:
                detected_format = self.format_manager.detect_format()
                if detected_format:
                    self.format = detected_format
                    self.format_manager.set_format(detected_format)
                else:
                    self.select_format()
                    if not self.format:
                        self._reset_state()
                        return

        # Reset selections
        self.selected_box_indices = set()
        self.manual_deselect_all = False
        self.image_selections = {}
        self._update_format_display()

        # Handle JSON class discovery
        logging.info(f"[LOAD_DATASET] Format detected: '{self.format}'. Checking for class discovery...")
        if self.format == 'JSON':
            logging.info("[LOAD_DATASET] Format is JSON, calling _handle_json_class_discovery...")
            self._handle_json_class_discovery()
        else:
            logging.info(f"[LOAD_DATASET] Format is {self.format}, showing class management dialog...")
            self._show_class_management_dialog()
        
        self._populate_image_jump_box()
        self.load_image()
        self.app_status_bar.set_status(get_status_message("dataset_loaded"))
        logging.info(f"Dataset loaded. Images: {len(self.image_files)}. Format: {self.format}.")

        # Populate the image jump box
        self._populate_image_jump_box()

    def _reset_state(self):
        """Reset application state when dataset loading is cancelled."""
        self.image_dir = None
        self.label_dir = None
        self.image_files = []
        self.current_index = 0
        self.canvas.image = None
        self.canvas.boxes = []
        self.canvas.selected_boxes = set()
        self.canvas.update()
        self.update_labels_panel([])
        self.update_status_label()
        self._update_format_display()
        self.app_status_bar.set_status(get_status_message("no_format"))
        logging.info("Application state reset")
    
    def _handle_json_class_discovery(self):
        """Handle JSON class discovery with progress dialog."""
        logging.info("[JSON_CLASS_DISCOVERY] Starting class discovery...")
        discovered = {}
        
        try:
            # Count JSON files
            files = [fn for fn in os.listdir(self.label_dir) if fn.endswith('.json')] if os.path.isdir(self.label_dir) else []
            logging.info(f"[JSON_CLASS_DISCOVERY] Found {len(files)} JSON files in {self.label_dir}")
            sample_count = min(len(files), 20)
            est_secs = max(0.2, sample_count * 0.02)
            
            # Show progress dialog
            pd = QProgressDialog(f"Scanning {sample_count} JSON files (est. {est_secs:.1f}s)...", None, 0, 0, self)
            pd.setWindowTitle("Inspecting JSON dataset")
            pd.setWindowModality(Qt.WindowModal)
            pd.setAutoClose(True)
            pd.show()
            QApplication.processEvents()

            # Detect JSON structure
            try:
                self.json_name_keys = self._detect_json_name_keys(self.label_dir)
                logging.info(f"[JSON_CLASS_DISCOVERY] Detected name keys: {self.json_name_keys}")
            except Exception as e:
                logging.warning(f"[JSON_CLASS_DISCOVERY] Failed to detect name keys: {e}")
                self.json_name_keys = ['className', 'category_name', 'name', 'label']

            try:
                self.json_bbox_methods = self._detect_json_bbox_style(self.label_dir)
            except Exception:
                self.json_bbox_methods = ['contour', 'bbox', 'points', 'xywh']

            # Discover classes
            discovered = self._discover_classes_in_json_folder(self.label_dir)
            logging.info(f"[JSON_CLASS_DISCOVERY] Discovery returned {len(discovered)} classes: {list(discovered.keys())[:20]}")
            
            # Close progress dialog
            try:
                pd.close()
            except Exception:
                pass

        except Exception as e:
            logging.error(f"[JSON_CLASS_DISCOVERY] Error during discovery: {e}")
            traceback.print_exc()
            try:
                if 'pd' in locals(): pd.close()
            except: pass

        # ALWAYS show the class discovery dialog for JSON format
        if discovered:
            logging.info(f"[JSON_CLASS_DISCOVERY] Showing dialog for {len(discovered)} classes...")
            result = self._prompt_use_discovered_json_classes(discovered)
            logging.info(f"[JSON_CLASS_DISCOVERY] Dialog result: {result}")
            if result:
                self.json_display_override = True
        else:
            logging.warning("[JSON_CLASS_DISCOVERY] No classes discovered, showing class management dialog instead")
            self._show_class_management_dialog()

    def _populate_image_jump_box(self):
        """Fills the image jump dropdown with the names of loaded images."""
        self.image_jump_box.blockSignals(True)
        self.image_jump_box.clear()
        items = [f"{i+1}: {os.path.basename(name)}" for i, name in enumerate(self.image_files)]
        logging.info(f"[IMAGE_JUMP] Populating with {len(items)} images")
        self.image_jump_box.addItems(items)
        self.image_jump_box.blockSignals(False)
        self.image_jump_box.update()  # Force UI update

    def _show_class_management_dialog(self):
        """Shows a dialog to display current classes and allow manual entry."""
        current_classes = self.class_manager.get_classes()
        dialog = ClassManagementDialog(current_classes, self)

        if dialog.exec_() == QDialog.Accepted:
            entered_classes = dialog.entered_classes
            if entered_classes:
                # User entered new classes, so we use them
                self.class_manager.set_classes(entered_classes)
                self.canvas.classes = entered_classes
                self.app_status_bar.set_status(f"Manually loaded {len(entered_classes)} classes.")
                logging.info(f"User entered {len(entered_classes)} new classes.")

                # Save the entered classes to a file for future use
                classes_dir = "user_classes"
                os.makedirs(classes_dir, exist_ok=True)
                file_path = os.path.join(classes_dir, "classes.txt")
                with open(file_path, "w") as f:
                    f.write("\n".join(entered_classes))
                logging.info(f"Saved manually entered classes to '{file_path}'.")
            else:
                # User clicked OK without entering new classes
                logging.info("User proceeded with existing classes.")

    def _discover_classes_in_json_folder(self, folder_path):
        # ONLY use keys that are likely to contain CLASS names, not file names
        # Priority order: className first, then category_name, then label
        class_name_keys = ['className', 'category_name', 'label', 'class_name', 'class']
        
        if not os.path.isdir(folder_path):
            return {}
        
        discovered = {}
        
        def looks_like_filename(s):
            """Check if string looks like a filename."""
            if not s:
                return True
            s_lower = s.lower()
            # Check for file extensions
            file_exts = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', '.tiff', '.webp', '.json', '.txt', '.xml']
            for ext in file_exts:
                if s_lower.endswith(ext):
                    return True
            # Check for patterns like "images123"
            if s_lower.startswith('image') and any(c.isdigit() for c in s):
                return True
            return False
        
        def add_count(name):
            if name and isinstance(name, str):
                normalized = name.strip()
                # Skip if it looks like an ID, filename, or is too short/long
                if normalized and not self._looks_like_id(normalized) and not looks_like_filename(normalized):
                    if len(normalized) >= 2 and len(normalized) <= 50:
                        discovered[normalized] = discovered.get(normalized, 0) + 1
        
        def extract_class_name(obj):
            """Extract class name from object, prioritizing className field."""
            if not isinstance(obj, dict):
                return None
            # Check keys in priority order
            for key in class_name_keys:
                if key in obj:
                    val = obj[key]
                    if isinstance(val, str) and val.strip():
                        return val.strip()
            return None
        
        def inspect_obj(o):
            if isinstance(o, dict):
                # Only extract from objects that look like annotations
                # (have classId or className or type field)
                if 'classId' in o or 'className' in o or 'category_id' in o or 'type' in o:
                    name = extract_class_name(o)
                    if name:
                        add_count(name)
                # Recurse into nested structures
                for v in o.values():
                    inspect_obj(v)
            elif isinstance(o, list):
                for item in o:
                    inspect_obj(item)
        
        files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        for fname in files[:100]:
            try:
                with open(os.path.join(folder_path, fname), 'r') as f:
                    data = json.load(f)
                    inspect_obj(data)
            except Exception as e:
                logging.debug(f"Error reading path {fname}: {e}")
                continue
        
        logging.info(f"[CLASS_DISCOVERY] Found classes: {list(discovered.keys())}")
        return discovered

    def _detect_json_bbox_style(self, folder_path, sample_limit=20):
        if not os.path.isdir(folder_path):
            return ['contour', 'bbox', 'points', 'xywh']
        
        files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        files = files[:sample_limit]
        
        style_counts = {'contour': 0, 'bbox': 0, 'points': 0, 'xywh': 0}
        coco_map = {}
        
        def inspect_obj(o):
            if isinstance(o, dict):
                if 'contour' in o and isinstance(o['contour'], dict) and 'points' in o['contour']:
                    style_counts['contour'] += 1
                if 'bbox' in o:
                    style_counts['bbox'] += 1
                if 'points' in o and isinstance(o['points'], list):
                    style_counts['points'] += 1
                if 'x' in o and 'y' in o and 'width' in o and 'height' in o:
                    style_counts['xywh'] += 1
                for v in o.values():
                    inspect_obj(v)
            elif isinstance(o, list):
                for item in o:
                    inspect_obj(item)
        
        for fname in files:
            try:
                with open(os.path.join(folder_path, fname), 'r') as f:
                    data = json.load(f)
                    # Extract COCO categories if present (Original Logic Restored)
                    if isinstance(data, dict) and 'categories' in data and isinstance(data['categories'], list):
                        for cat in data['categories']:
                            if isinstance(cat, dict):
                                cid = cat.get('id') or cat.get('category_id')
                                name = cat.get('name') or cat.get('label')
                                if cid is not None and name:
                                    try:
                                        coco_map[int(cid)] = str(name)
                                    except:
                                        pass
                    inspect_obj(data)
            except:
                continue
                
        if coco_map:
            setattr(self, 'json_coco_category_map', coco_map)
            logging.info(f"Detected COCO category map with {len(coco_map)} entries.")

        sorted_styles = sorted(style_counts.items(), key=lambda x: x[1], reverse=True)
        return [s[0] for s in sorted_styles if s[1] > 0] or ['contour', 'bbox', 'points', 'xywh']

    def _detect_json_name_keys(self, folder_path, sample_limit=20):
        if not os.path.isdir(folder_path):
            return ['className', 'category_name', 'name', 'label']
        files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        files = files[:sample_limit]
        key_counts = {}
        nested_counts = {}
        
        def inspect_obj(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if isinstance(v, str) and len(v) < 50:
                        key_counts[k] = key_counts.get(k, 0) + 1
                    elif isinstance(v, dict) and 'name' in v:
                        nested_key = f"{k}.name"
                        nested_counts[nested_key] = nested_counts.get(nested_key, 0) + 1
                    inspect_obj(v)
            elif isinstance(o, list):
                for item in o:
                    inspect_obj(item)
                    
        for fname in files:
            try:
                with open(os.path.join(folder_path, fname), 'r') as f:
                    data = json.load(f)
                    inspect_obj(data)
            except:
                continue
        
        all_keys = {**key_counts, **nested_counts}
        sorted_keys = sorted(all_keys.items(), key=lambda x: x[1], reverse=True)
        result = [k[0] for k in sorted_keys if k[1] > 0]
        defaults = ['className', 'category_name', 'name', 'label']
        for d in defaults:
            if d not in result:
                result.append(d)
        return result[:10]
    #     return None
    def _get_name_from_object(self, obj):
        if not isinstance(obj, dict):
             return None
        keys = getattr(self, 'json_name_keys', ['className', 'category_name', 'name', 'label'])
        for key in keys:
            if '.' in key:
                parts = key.split('.')
                val = obj
                for part in parts:
                    if isinstance(val, dict) and part in val:
                        val = val[part]
                    else:
                        val = None
                        break
                if val and isinstance(val, str):
                    return val
            elif key in obj:
                val = obj[key]
                if isinstance(val, str):
                    return val
        return None

    def _normalize_label(self, name):
        if not isinstance(name, str):
            return None
        s = name.strip().lower()
        s = re.sub(r"[^a-z0-9]+", ' ', s)
        s = re.sub(r"\s+", ' ', s).strip()
        return s

    def _looks_like_id(self, s):
        if not isinstance(s, str):
            return False
        s = s.strip()
        if not s:
            return False
        # UUID pattern
        if re.match(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', s):
            return True
        # long hex-like strings
        if len(s) >= 20 and re.fullmatch(r'[0-9a-fA-F\-]+', s):
            return True
        return False

    def _prompt_use_discovered_json_classes(self, discovered):
        """Show a dialog listing discovered classes and allow user to rename/confirm them."""
        if not discovered:
            return False

        # Create dialog with editable fields per discovered class
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Discovered Classes - Confirm / Edit")
        dlg.setMinimumWidth(500)
        dlg.setMinimumHeight(400)

        main_layout = QVBoxLayout(dlg)
        
        # Info label
        info = QLabel(f"Found {len(discovered)} classes in annotation files.\nYou can edit any name before applying.\nLeave blank to use the original name.")
        main_layout.addWidget(info)
        
        # Scroll area for many classes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        form = QFormLayout(scroll_widget)
        
        edits = {}
        for name in sorted(discovered.keys()):
            le = QLineEdit(name)
            form.addRow(f"{name}:", le)
            edits[name] = le
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
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
        for orig in sorted(discovered.keys()):
            val = edits[orig].text().strip()
            if not val:
                val = orig
            # de-dup by appending suffix if necessary
            if val in seen:
                suffix = 1
                new_val = f"{val}_{suffix}"
                while new_val in seen:
                    suffix += 1
                    new_val = f"{val}_{suffix}"
                val = new_val
            seen.add(val)
            edited.append(val)

        # Apply classes for display
        self.class_manager.classes = edited
        self.canvas.classes = edited

        # Remap existing canvas boxes to the newly confirmed classes when possible
        try:
            self._remap_canvas_boxes_using_json_names()
        except Exception:
            logging.debug("_remap_canvas_boxes_using_json_names failed")

        # Refresh UI now that classes + box ids are consistent
        self.update_labels_panel(self.canvas.boxes)
        self.app_status_bar.set_status(f"Loaded {len(edited)} classes from JSON for display.")
        logging.info(f"Loaded {len(edited)} classes from JSON for display. Classes: {edited}")
        return True

    def _apply_discovered_json_classes(self, discovered):
        """Apply discovered classes for display without blocking the UI.

        This sets the in-memory classes used for display (class_manager + canvas)
        but does not overwrite persistent classes.txt on disk. It logs what was
        applied so the user can still change them later.
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
        # Apply classes for display only (do not refresh labels panel here).
        # The calling flow (load_dataset -> load_image) will refresh the image and
        # labels; avoiding an immediate update prevents selection/refresh races.
        self.class_manager.classes = applied
        self.canvas.classes = applied
        self.app_status_bar.set_status(f"Loaded {len(applied)} classes from JSON for display.")
        logging.info(f"Auto-applied {len(applied)} discovered JSON classes for display: {applied}")
        return True

    def _remap_canvas_boxes_using_json_names(self):
        """Attempt to remap numeric class ids of current canvas.boxes using JSON names.

        For each box on the current image, query the per-image JSON for a textual
        class name. If found and it maps to one of the current classes (exact or
        normalized match), set the box's class index to that value. This keeps the
        canvas numeric ids aligned with the displayed textual classes.
        """
        if not self.image_files:
            return
        img_name = self.image_files[self.current_index]
        classes_list = self.class_manager.get_classes()
        if not classes_list:
            return

        # build normalized lookup
        norm_map = {self._normalize_label(n): i for i, n in enumerate(classes_list)}

        new_boxes = []
        for b in self.canvas.boxes:
            x, y, w, h, old_cls = b
            try:
                json_name = self._get_json_classname_for_box(img_name, b)
            except Exception:
                json_name = None

            new_cls = old_cls
            if isinstance(json_name, str) and json_name.strip():
                t = json_name.strip()
                if t in classes_list:
                    new_cls = classes_list.index(t)
                else:
                    norm = self._normalize_label(t)
                    if norm in norm_map:
                        new_cls = norm_map[norm]

            new_boxes.append((x, y, w, h, new_cls))

        # apply and mark changed
        self.canvas.boxes = new_boxes
        self.canvas.changed = True

    # ----------------------------------------------------------------
    def _detect_format(self):
        """Auto-detect annotation format from files in the current label folder.

        Returns one of: 'TXT', 'JSON', 'COCO' or None if detection fails.
        """
        try:
            if not self.label_dir or not os.path.isdir(self.label_dir):
                return None
            files = os.listdir(self.label_dir)
            # COCO: look for a single COCO file
            for fn in files:
                if fn.endswith('.coco.json') or fn == '_annotations.coco.json' or fn.endswith('_annotations.coco.json'):
                    return 'COCO'
            # TXT files present
                if any(fn.endswith('.txt') for fn in files):
                    return 'TXT'
                # JSON files present
                if any(fn.endswith('.json') for fn in files):
                    return 'JSON'
        except Exception:
            pass
        return None

    def _create_initial_files(self):
        """Create initial annotation files based on selected format."""
        try:
            if self.format == "TXT":
                # Create empty .txt files for each image
                for img_file in self.image_files:
                    base_name = os.path.splitext(img_file)[0]
                    txt_file = os.path.join(self.label_dir, base_name + ".txt")
                    if not os.path.exists(txt_file):
                        with open(txt_file, 'w') as f:
                            f.write("")  # Create empty file
                logging.info(f"Created {len(self.image_files)} empty TXT files")
                QMessageBox.information(self, "Files Created", 
                    f"Created {len(self.image_files)} TXT files in:\n{self.label_dir}\n\nYou can now start annotating!")
            
            elif self.format == "JSON":
                # Create empty .json files for each image
                for img_file in self.image_files:
                    base_name = os.path.splitext(img_file)[0]
                    json_file = os.path.join(self.label_dir, base_name + ".json")
                    if not os.path.exists(json_file):
                        with open(json_file, 'w') as f:
                            json.dump({"annotations": []}, f)
                logging.info(f"Created {len(self.image_files)} empty JSON files")
                QMessageBox.information(self, "Files Created", 
                    f"Created {len(self.image_files)} JSON files in:\n{self.label_dir}\n\nYou can now start annotating!")
            
            elif self.format == "COCO":
                # Create single COCO file
                coco_file = os.path.join(self.label_dir, "_annotations.coco.json")
                coco_data = {
                    "info": {"description": "Dataset", "version": "1.0", "year": 2024},
                    "licenses": [],
                    "images": [],
                    "annotations": [],
                    "categories": []
                }
                with open(coco_file, 'w') as f:
                    json.dump(coco_data, f, indent=2)
                logging.info(f"Created COCO annotation file: {coco_file}")
                QMessageBox.information(self, "File Created", 
                    f"Created COCO file:\n{coco_file}\n\nYou can now start annotating!")
        
        except Exception as e:
            logging.error(f"Error creating initial files: {e}")
            QMessageBox.warning(self, "Error", f"Failed to create files:\n{str(e)}")

    def select_format(self):
        """Prompt the user to choose the annotation format (TXT/JSON/COCO)."""
        fmt_box = QMessageBox(self)
        fmt_box.setWindowTitle("Select Annotation Format")
        fmt_box.setText("Choose the annotation format for this dataset:")
        fmt_box.setIcon(QMessageBox.Question)
        fmt_box.setStandardButtons(QMessageBox.NoButton)
        fmt_box.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)

        txt_btn = fmt_box.addButton("TXT (.txt)", QMessageBox.ActionRole)
        json_btn = fmt_box.addButton("JSON (.json)", QMessageBox.ActionRole)
        coco_btn = fmt_box.addButton("COCO (_annotations.coco.json)", QMessageBox.ActionRole)
        cancel_btn = fmt_box.addButton("Cancel", QMessageBox.RejectRole)

        fmt_box.setDefaultButton(cancel_btn)
        fmt_box.exec_()

        clicked = fmt_box.clickedButton()
        if clicked == cancel_btn or clicked is None:
            logging.info("Format selection cancelled by user.")
            self.app_status_bar.set_status("Format selection cancelled.")
            return

        new_format = None
        if clicked == txt_btn:
            new_format = "TXT"
        elif clicked == json_btn:
            new_format = "JSON"
        elif clicked == coco_btn:
            new_format = "COCO"

        if new_format:
            self.format = new_format
            self._update_format_display()
            logging.info(f"Format changed to {self.format}. Now loading dataset...")
            self.reload_data_for_new_format()
            self.app_status_bar.set_format(self.format)
            self.app_status_bar.set_status(get_status_message("format_selected"))


    def _update_format_display(self):
        """Updates the format display label in the control panel."""
        if self.current_format_display:
            self.current_format_display.setText(f"Current Format: {self.format or 'None'}")

    # ----------------------------------------------------------------
    def set_edit_mode(self):
        self.mode = "edit"
        self.canvas.mode = "edit"
        # Auto-enable drawing mode so user can immediately draw
        self.canvas.set_drawing_mode(True)
        self.update_status_label()
        self.app_status_bar.set_mode("edit")
        self.app_status_bar.set_status("Edit Mode Enabled. Click and drag to draw boxes. Press 'X' to disable drawing.")

    def set_view_mode(self):
        self.mode = "view"
        self.canvas.mode = "view"
        self.update_status_label()
        self.app_status_bar.set_mode("view")
        self.app_status_bar.set_status(get_status_message("view_mode_enabled"))
    
    def update_status_label(self):
        """Update status label to show current mode and info."""
        if not self.image_files:
            mode_text = "EDIT MODE" if self.mode == "edit" else "VIEW MODE"
            self.status_label.setText(mode_text)
            return
        
        current_pos = self.current_index + 1
        total_images = len(self.image_files)
        img_name = self.image_files[self.current_index]
        box_count = len(self.canvas.boxes)
        
        mode_indicator = "EDIT MODE" if self.mode == "edit" else "VIEW MODE"
        self.status_label.setText(
            f"[{current_pos}/{total_images}] {img_name} ({box_count} boxes) | {mode_indicator} | Format: {self.format}"
        )
        
        # Update status bar
        self.app_status_bar.set_image_info(current_pos, total_images, img_name)
        self.app_status_bar.set_box_count(box_count)
        if self.format:
            self.app_status_bar.set_format(self.format)
        
        # Style status bar - orange background for edit mode
        if self.mode == "edit":
            self.status_label.setStyleSheet(
                "background-color: #ff9800; color: white; padding: 8px; font-weight: bold; border-radius: 4px;"
            )
        else:
            self.status_label.setStyleSheet(
                "background-color: #2196F3; color: white; padding: 8px; font-weight: bold; border-radius: 4px;"
            )

    
    def init_shortcuts(self):
        """Initialize application-wide shortcuts."""
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence

        # Navigation
        self.shortcut_next = QShortcut(QKeySequence(Qt.Key_D), self)
        self.shortcut_next.activated.connect(self.next_image_action)
        
        self.shortcut_prev = QShortcut(QKeySequence(Qt.Key_A), self)
        self.shortcut_prev.activated.connect(self.prev_image_action)

        # Actions
        self.shortcut_save = QShortcut(QKeySequence(Qt.Key_S), self)
        self.shortcut_save.activated.connect(self.save_action)
        
        self.shortcut_delete = QShortcut(QKeySequence(Qt.Key_Delete), self)
        self.shortcut_delete.activated.connect(self.delete_action)
        
        self.shortcut_cancel = QShortcut(QKeySequence(Qt.Key_C), self)
        self.shortcut_cancel.activated.connect(self.cancel_action)
        
        self.shortcut_view = QShortcut(QKeySequence(Qt.Key_X), self)
        self.shortcut_view.activated.connect(self.view_mode_action)
        
        self.shortcut_quit = QShortcut(QKeySequence(Qt.Key_Q), self)
        self.shortcut_quit.activated.connect(self.close_prompt_action)

    # Wrapper actions for shortcuts
    def next_image_action(self):
        logging.info(f"[SHORTCUT] D key pressed: Next Image (image_files={len(self.image_files) if self.image_files else 0}, current_index={self.current_index})")
        self.next_image()

    def prev_image_action(self):
        logging.info(f"[SHORTCUT] A key pressed: Prev Image (image_files={len(self.image_files) if self.image_files else 0}, current_index={self.current_index})")
        self.prev_image()

    def save_action(self):
        logging.info("Shortcut S pressed: Save")
        self.save_annotation()

    def delete_action(self):
        if self.mode == "edit":
            self.delete_selected_boxes()

    def view_mode_action(self):
        logging.info("Shortcut X pressed: Switching to View Mode")
        self.set_view_mode()

    def cancel_action(self):
        if self.mode == "edit":
            logging.info("Shortcut C pressed: Cancel annotation")
            if self.canvas.current_polygon:
                self.canvas.current_polygon = []
                self.canvas.update()
                self.app_status_bar.set_status("Cancelled incomplete polygon.")
            elif self.canvas.current_box:
                self.canvas.current_box = None
                self.canvas.start_pos = None
                self.canvas.update()
                self.app_status_bar.set_status("Cancelled incomplete box.")

    def close_prompt_action(self):
        self.close_prompt()

    # ----------------------------------------------------------------
    # keyPressEvent replaced by QShortcuts in init_shortcuts()
    # Keeping minimal pass for unhandled keys if needed, or removing entirely.
    def keyPressEvent(self, e):
        # Fallback for keys not covered by shortcuts if any
        super().keyPressEvent(e)

    def close_prompt(self):
        reply = QMessageBox.question(
            self, "Exit", "Are you sure you want to quit?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.close()

    # ----------------------------------------------------------------
    # ----------------------------------------------------------------
    def on_polygon_added(self, poly):
        """Called when a polygon is added to canvas. Show class selection dialog."""
        if self.mode != "edit":
             return

        # Show class selection dialog
        classes = self.class_manager.get_classes()
        dialog = ClassSelectionDialog(classes, self)
        
        if dialog.exec_() == QDialog.Accepted:
            # Resolve selected class name -> id
            try:
                selected_name = dialog.class_combo.currentText()
                if selected_name in classes:
                    class_id = classes.index(selected_name)
                else:
                    class_id = 0 # Default
                
                # Update the LAST polygon (we just added it)
                if self.canvas.polygons:
                    pts, _ = self.canvas.polygons[-1]
                    self.canvas.polygons[-1] = (pts, class_id)
                    logging.info(f"Assigned class '{selected_name}' (id={class_id}) to new polygon.")
                    
                    # Auto-select the newly added polygon
                    # Index is number of boxes + index of this polygon (which is last, so len - 1)
                    new_poly_idx = len(self.canvas.boxes) + len(self.canvas.polygons) - 1
                    self.selected_box_indices.add(new_poly_idx)
                    self.image_selections[self.current_index] = self.selected_box_indices.copy()
                    
                    # Trigger auto-save ONLY if auto-save checkbox is enabled
                    if self.auto_save_cb.isChecked():
                        self.canvas.changed = True
                        self.canvas.update()
                        self.update_labels_panel(self.canvas.boxes)
                        self.save_annotation(auto=True)
                    else:
                        self.canvas.changed = True
                        self.canvas.update()
                        self.update_labels_panel(self.canvas.boxes)
                    return
                    
            except Exception as e:
                logging.error(f"Error selecting class for polygon: {e}")
        else:
            # User cancelled - remove the polygon that was just added
            if self.canvas.polygons:
                self.canvas.polygons.pop()
                logging.info("Class selection cancelled. Removed unclassified polygon.")
        
        self.canvas.changed = True
        self.canvas.update()
        self.update_labels_panel(self.canvas.boxes) # Refresh list

    def on_box_added(self, box):
        """Called when a box is added to canvas. Show class selection dialog."""
        if self.mode != "edit":
            if self.prompt_switch_to_edit_mode():
                self.canvas.mode = "edit" # Ensure canvas mode is also updated
            return
        
        # Show class selection dialog
        classes = self.class_manager.get_classes()
        dialog = ClassSelectionDialog(classes, self)
        
        if dialog.exec_() == QDialog.Accepted:
            # Resolve selected class name -> id (ensure JSON uses numeric category_id)
            try:
                selected_name = dialog.class_combo.currentText()
            except Exception:
                selected_name = None

            classes = self.class_manager.get_classes()
            if selected_name and selected_name in classes:
                class_idx = classes.index(selected_name)
            else:
                # Fallback to index if dialog provides it
                class_idx = dialog.get_selected_class()

            # Update the box with the selected class id
            x, y, w, h, _ = box
            self.canvas.boxes[-1] = (x, y, w, h, class_idx)
            self.canvas.changed = True
            
            # Make the newly added box visible/selected according to current selection
            new_idx = len(self.canvas.boxes) - 1
            # Always include the newly created box in the visible selection set so
            # it appears immediately regardless of prior select/deselect state.
            # This matches expected UX: when you draw a box it should be visible.
            self.selected_box_indices.add(new_idx)

            # Prepare bbox info for logging based on format
            log_bbox_info = ""
            if self.format == "TXT":
                img_h, img_w = self.canvas.image.shape[:2]
                xc = (x + w / 2) / img_w
                yc = (y + h / 2) / img_h
                bw = w / img_w
                bh = h / img_h
                log_bbox_info = f"bbox=(class={class_idx} xc={xc:.6f} yc={yc:.6f} bw={bw:.6f} bh={bh:.6f})"
            else:
                log_bbox_info = f"class={class_idx} bbox=({x:.1f},{y:.1f},{w:.1f},{h:.1f})"

            # Terminal log: box added
            img_name = self.image_files[self.current_index] if self.image_files else "<no-image>"
            logging.info(f"Image '{img_name}': added bbox idx={new_idx} {log_bbox_info}")


            # Save immediately to file
            self.save_bbox_to_file(class_idx, x, y, w, h)
            
            # Update labels panel
            self.update_labels_panel(self.canvas.boxes)
            # Ensure canvas reflects the updated selection
            self.canvas.selected_boxes = self.selected_box_indices
            self.canvas.update()

            # Persist per-image selection state
            self.image_selections[self.current_index] = self.selected_box_indices.copy()
        else:
            # User cancelled - remove the box
            self.canvas.boxes.pop()
            self.canvas.changed = True
            self.canvas.update()
            img_name = self.image_files[self.current_index] if self.image_files else "<no-image>"
            logging.info(f"Image '{img_name}': bbox creation cancelled by user.")

    def _prompt_for_manual_classes(self):
        """Opens a dialog for the user to manually enter class names."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Enter Class Names")
        dialog_layout = QVBoxLayout()
        
        label = QLabel("Enter class names, one per line:")
        dialog_layout.addWidget(label)
        
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("e.g.,\nperson\ncar\nbicycle")
        dialog_layout.addWidget(text_edit)
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        dialog_layout.addWidget(ok_button)
        
        dialog.setLayout(dialog_layout)
        if dialog.exec_() == QDialog.Accepted:
            entered_classes = [line.strip() for line in text_edit.toPlainText().split('\n') if line.strip()]
            if not entered_classes:
                self.app_status_bar.set_status("No classes entered.")
                return

            self.class_manager.set_classes(entered_classes)
            self.canvas.classes = entered_classes
            self.app_status_bar.set_status(f"Manually loaded {len(entered_classes)} classes.")

            # Save the entered classes to a file for future use
            classes_dir = "user_classes"
            os.makedirs(classes_dir, exist_ok=True)
            file_path = os.path.join(classes_dir, "classes.txt")
            with open(file_path, "w") as f:
                f.write("\n".join(entered_classes))
            logging.info(f"Saved {len(entered_classes)} manually entered classes to '{file_path}'.")

    def save_bbox_to_file(self, class_idx, x, y, w, h):
        """Save bbox coordinates and class to txt file."""
        if not self.image_files or not self.format or not self.label_dir:
            return
        
        img_name = self.image_files[self.current_index]
        os.makedirs(self.label_dir, exist_ok=True)
        
        if self.format == "TXT":
            label_file = os.path.join(self.label_dir, os.path.splitext(img_name)[0] + ".txt")
            img_h, img_w = self.canvas.image.shape[:2]
            xc = (x + w / 2) / img_w
            yc = (y + h / 2) / img_h
            bw = w / img_w
            bh = h / img_h
            
            with open(label_file, "a") as f:
                f.write(f"{class_idx} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")
        elif self.format == "JSON":
            # For JSON and COCO, it's better to save the entire file at once.
            # We can call the main save function here.
            self.save_annotation(auto=True)
        elif self.format == "COCO":
            self.save_annotation(auto=True)

    # ----------------------------------------------------------------
    def load_image(self):
        """Load image + annotations if available."""
        if not self.image_files:
            return

        img_name = self.image_files[self.current_index]
        img_path = os.path.join(self.image_dir, img_name)

        # load the image into canvas
        self.canvas.load_image(img_path)

        boxes = []
        polygons = []
        img_shape = self.canvas.image.shape[:2]

        if self.format == "TXT":
            file = os.path.join(self.label_dir, os.path.splitext(img_name)[0] + ".txt")
            if os.path.exists(file):
                boxes, polygons = load_txt_annotations(file, img_shape, mode=self.annotation_mode)

        elif self.format == "JSON":
            file = os.path.join(self.label_dir, os.path.splitext(img_name)[0] + ".json")
            if not os.path.exists(file):
                 # Check in converted_json subfolder
                 file = os.path.join(self.label_dir, "converted_json", os.path.splitext(img_name)[0] + ".json")
            
            if os.path.exists(file):
                boxes, polygons = load_json_annotations(file, img_name, self.class_manager, img_shape, mode=self.annotation_mode)
                
        elif self.format == "COCO":
            file = os.path.join(self.label_dir, "_annotations.coco.json")
            if os.path.exists(file):
                # We need to map COCO categories if possible?
                # The loader currently returns class_id.
                # AppWindow usually handles COCO alignment (loading names from file).
                # But to save lines, we assume ClassManager is already aligned or we accept IDs.
                boxes, polygons = load_coco_annotations(file, img_name, self.class_manager, mode=self.annotation_mode)

        # now push them into the canvas
        self.canvas.boxes = boxes
        self.canvas.polygons = polygons
        self.canvas.update()
        
        # Log summary
        src = file if 'file' in locals() and os.path.exists(file) else '<not-found>'
        classes = self.class_manager.get_classes()
        logging.info(f"Loaded {len(boxes)} boxes and {len(polygons)} polygons from '{src}'")
        
        logging.info(f"[LOAD_IMAGE] About to set selections: total boxes loaded = {len(boxes)}")
        logging.info(f"[LOAD_IMAGE] current_index={self.current_index}, current selected_box_indices={self.selected_box_indices}")
        logging.info(f"[LOAD_IMAGE] Has this image been visited before? {self.current_index in self.image_selections}")

        # Determine if we should restore from history or select fresh
        # If selected_box_indices is empty, it means we're navigating to a new image
        # OR it's the first load of the app
        if len(self.selected_box_indices) == 0:
            # No selections set - this is a fresh load of this image
            if self.current_index in self.image_selections:
                # We've visited this image before - restore previous selections
                saved_selections = self.image_selections[self.current_index]
                # Allow indices for both boxes and polygons
                total_items = len(boxes) + len(polygons)
                valid_selections = {idx for idx in saved_selections if idx < total_items}
                self.selected_box_indices = valid_selections
                logging.info(f"[LOAD_IMAGE] REVISITING IMAGE: Restored {len(valid_selections)}/{total_items} items from history. selected_box_indices={self.selected_box_indices}")
            else:
                # First time visiting this image - select all boxes AND polygons by default
                if self.manual_deselect_all:
                    self.selected_box_indices = set()  # Respect user's choice to deselect
                    logging.info(f"[LOAD_IMAGE] FIRST VISIT + manual_deselect_all=True: selected_box_indices={self.selected_box_indices}")
                else:
                    total_items = len(boxes) + len(polygons)
                    self.selected_box_indices = set(range(total_items))  # Default to all selected
                    logging.info(f"[LOAD_IMAGE] FIRST VISIT + manual_deselect_all=False: selected_box_indices={self.selected_box_indices} (range 0-{total_items-1})")
                    
                    if len(self.selected_box_indices) != total_items:
                        logging.error(f"[LOAD_IMAGE] MISMATCH! range({total_items}) produced {len(self.selected_box_indices)} indices")
        else:
            # Selections are already set - likely pre-set by code (or persisted incorrectly)
            # Validate them against current item count
            total_items = len(boxes) + len(polygons)
            valid_selections = {idx for idx in self.selected_box_indices if idx < total_items}
            
            if len(valid_selections) != len(self.selected_box_indices):
                logging.warning(f"[LOAD_IMAGE] Pruned {len(self.selected_box_indices) - len(valid_selections)} invalid indices. New count: {len(valid_selections)}")
                self.selected_box_indices = valid_selections
            logging.info(f"[LOAD_IMAGE] Selections already set: {self.selected_box_indices}")
        
        # Always save final selections for this image
        self.image_selections[self.current_index] = self.selected_box_indices.copy()
        
        # Update labels panel
        self.update_labels_panel(boxes)
        
        # Update status label
        self.update_status_label()
        
        # Update the jump box to reflect the current image without triggering a jump
        self.image_jump_box.blockSignals(True)
        self.image_jump_box.setCurrentIndex(self.current_index)
        self.image_jump_box.blockSignals(False)

    # ----------------------------------------------------------------
    def update_labels_panel(self, boxes=None):
        """Update the labels list panel with all current boxes AND polygons."""
        # Use canvas data directly if boxes arg is not the full picture
        current_boxes = self.canvas.boxes
        current_polygons = self.canvas.polygons
        
        self.labels_list.blockSignals(True)
        self.labels_list.clear()

        classes = self.class_manager.get_classes()
        
        # 1. Add Boxes
        for idx, box in enumerate(current_boxes):
            # box format: (x, y, w, h, cls)
            try:
                class_idx = int(box[4])
            except Exception:
                class_idx = None

            class_name = self._resolve_class_name(class_idx, box, classes, idx)
            is_checked = idx in self.selected_box_indices
            
            self._add_label_item(idx, class_name, is_checked)

        # 2. Add Polygons
        # Offset index by len(boxes)
        box_count = len(current_boxes)
        for i, (pts, class_id) in enumerate(current_polygons):
            u_idx = box_count + i
            
            # Resolve class name for polygon
            try:
                c_idx = int(class_id) if class_id is not None else 0
            except:
                c_idx = 0
            
            if 0 <= c_idx < len(classes):
                c_name = classes[c_idx]
            else:
                c_name = f"Class {c_idx}"
            
            display_name = f"[Poly] {c_name}"
            is_checked = u_idx in self.selected_box_indices
            
            self._add_label_item(u_idx, display_name, is_checked)

        self.labels_list.blockSignals(False)
        self.canvas.selected_boxes = self.selected_box_indices
        self.canvas.update()

    def _resolve_class_name(self, class_idx, box, classes, idx):
        """Helper to resolve class name for boxes."""
        class_name = None
        
        # JSON override logic
        if self.format == 'JSON':
            img_name = self.image_files[self.current_index] if self.image_files else None
            try:
                json_name = self._get_json_classname_for_box(img_name, box)
                if json_name:
                     # Simplified override logic for brevity
                     if getattr(self, 'json_display_override', False):
                         return json_name
                     # Fallback if numeric invalid
                     if not (isinstance(class_idx, int) and 0 <= class_idx < len(classes)):
                         return json_name
            except Exception:
                pass

        if isinstance(class_idx, int) and 0 <= class_idx < len(classes):
            return classes[class_idx]
        
        return f"Class {class_idx if class_idx is not None else '?'}"

    def _add_label_item(self, idx, text, is_checked):
        """Helper to add item to list."""
        item = QListWidgetItem()
        widget = LabelListItemWidget(idx, text, is_checked, self.labels_list)
        widget.selection_toggled.connect(self.on_label_toggled_from_widget)
        widget.delete_requested.connect(self.delete_specific_box)
        widget.label_clicked.connect(self.on_label_clicked_from_widget)
        item.setSizeHint(widget.sizeHint())
        self.labels_list.addItem(item)
        item.setData(Qt.UserRole, idx)
        self.labels_list.setItemWidget(item, widget)

    def delete_specific_box(self, u_idx):
        """Delete specific box OR polygon by unified index."""
        box_count = len(self.canvas.boxes)
        
        if u_idx < box_count:
            # Delete box
            if 0 <= u_idx < box_count:
                self.canvas.boxes.pop(u_idx)
        else:
            # Delete polygon
            p_idx = u_idx - box_count
            if 0 <= p_idx < len(self.canvas.polygons):
                self.canvas.polygons.pop(p_idx)

        # Re-calculate selection indices (shift down)
        new_selections = set()
        for s in self.selected_box_indices:
            if s == u_idx:
                continue
            if s > u_idx:
                new_selections.add(s - 1)
            else:
                new_selections.add(s)
        
        self.selected_box_indices = new_selections
        self.canvas.changed = True
        self.update_labels_panel(self.canvas.boxes) # Refresh full list

    def on_label_toggled_from_widget(self, box_idx, is_checked):
        """Handle label checkbox toggle."""
        if is_checked:
            self.selected_box_indices.add(box_idx)
        else:
            self.selected_box_indices.discard(box_idx)
        self._update_selection_state(box_idx, is_checked)

    def on_label_clicked_from_widget(self, box_idx, event):
        """Handle click on label text."""
        if event.modifiers() & Qt.ControlModifier:
            is_checked = box_idx in self.selected_box_indices
            self._update_selection_state(box_idx, not is_checked)
        else:
            self.selected_box_indices = {box_idx}
            self.update_labels_panel(self.canvas.boxes)
        
        self.image_selections[self.current_index] = self.selected_box_indices.copy()

    def _update_selection_state(self, box_idx, is_checked):
        if is_checked:
             self.selected_box_indices.add(box_idx)
             if self.manual_deselect_all: self.manual_deselect_all = False
        else:
             self.selected_box_indices.discard(box_idx)
        
        self.canvas.selected_boxes = self.selected_box_indices
        self.canvas.update()
        self.image_selections[self.current_index] = self.selected_box_indices.copy()

    def on_label_toggled(self, item):
        """
        This method is kept for compatibility but should ideally not be triggered
        if using setItemWidget with custom checkboxes.
        The actual toggle logic is now in on_label_toggled_from_widget.
        """
        logging.warning("on_label_toggled (QListWidget signal) triggered. This should ideally be handled by custom widget signal.")
        box_idx = item.data(Qt.UserRole)
        is_checked = item.checkState() == Qt.Checked
        self._update_selection_state(box_idx, is_checked)

    def select_all_labels(self):
        """Check all labels."""
        self.manual_deselect_all = False  # Reset flag - user clicked "Select All"
        self.labels_list.blockSignals(True)
        for i in range(self.labels_list.count()):
            item = self.labels_list.item(i)
            widget = self.labels_list.itemWidget(item)
            if widget and isinstance(widget, LabelListItemWidget):
                # Avoid emitting the widget's stateChanged signal while programmatically setting state
                try:
                    widget.checkbox.blockSignals(True)
                    widget.checkbox.setChecked(True)
                finally:
                    widget.checkbox.blockSignals(False)
            # Fallback for old items if any
            item.setCheckState(Qt.Checked)
            # Prefer the widget's stored index; fall back to item data
            try:
                if widget and hasattr(widget, 'idx'):
                    box_idx = widget.idx
                else:
                    box_idx = item.data(Qt.UserRole)
            except Exception:
                box_idx = None
            if isinstance(box_idx, int):
                self.selected_box_indices.add(box_idx)
        self.labels_list.blockSignals(False)
        self.canvas.selected_boxes = self.selected_box_indices
        self.canvas.update()
        self.app_status_bar.set_status(get_status_message("all_selected"))

    def deselect_all_labels(self):
        """Uncheck all labels."""
        self.manual_deselect_all = True  # Mark that user deselected all
        self.selected_box_indices = set()  # Clear selections FIRST
        self.labels_list.blockSignals(True)
        for i in range(self.labels_list.count()):
            item = self.labels_list.item(i) # Get the QListWidgetItem
            widget = self.labels_list.itemWidget(item) # Get the custom widget
            if widget and isinstance(widget, LabelListItemWidget):
                try:
                    widget.checkbox.blockSignals(True)
                    widget.checkbox.setChecked(False)
                finally:
                    widget.checkbox.blockSignals(False)
            # Fallback for old items if any
            item.setCheckState(Qt.Unchecked)
        self.labels_list.blockSignals(False)
        self.canvas.selected_boxes = self.selected_box_indices
        self.canvas.update()
        
        # Persist the deselected state for the current image
        self.image_selections[self.current_index] = self.selected_box_indices.copy()
        self.app_status_bar.set_status(get_status_message("all_deselected"))

    # ----------------------------------------------------------------
    # ----------------------------------------------------------------
    def next_image(self):
        if not self.image_files:
            return
        # Check for incomplete polygon and prompt user
        if self.canvas.current_polygon and len(self.canvas.current_polygon) >= 3:
            reply = QMessageBox.question(
                self, "Incomplete Polygon",
                "You have an incomplete polygon. Do you want to complete and save it?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                # Complete the polygon and show class dialog
                pts = list(self.canvas.current_polygon)
                self.canvas.current_polygon = []
                new_poly = (pts, 0)
                self.canvas.polygons.append(new_poly)
                self.on_polygon_added(new_poly)
                return  # Don't navigate yet, let user finish class selection
            elif reply == QMessageBox.Cancel:
                return  # Don't navigate
            else:  # No
                self.canvas.current_polygon = []
                logging.info("User chose not to save incomplete polygon.")
        elif self.canvas.current_polygon:
            # Less than 3 points, just clear
            self.canvas.current_polygon = []
            logging.info("Cleared incomplete polygon when navigating to next image.")
        
        if self.canvas.changed:
            self.prompt_save_changes()
        
        # Save current selections
        self.image_selections[self.current_index] = self.selected_box_indices.copy()
        
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.logging_nav_status()
            
            # Restore selections if any
            self.selected_box_indices = set()
            if self.current_index in self.image_selections:
                self.selected_box_indices = self.image_selections[self.current_index].copy()
            else:
                 self.selected_box_indices = set()

            self.load_image()
        else:
            self.app_status_bar.set_status("Already at the last image.")

    def prev_image(self):
        if not self.image_files:
            return
        # Check for incomplete polygon and prompt user
        if self.canvas.current_polygon and len(self.canvas.current_polygon) >= 3:
            reply = QMessageBox.question(
                self, "Incomplete Polygon",
                "You have an incomplete polygon. Do you want to complete and save it?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                # Complete the polygon and show class dialog
                pts = list(self.canvas.current_polygon)
                self.canvas.current_polygon = []
                new_poly = (pts, 0)
                self.canvas.polygons.append(new_poly)
                self.on_polygon_added(new_poly)
                return  # Don't navigate yet, let user finish class selection
            elif reply == QMessageBox.Cancel:
                return  # Don't navigate
            else:  # No
                self.canvas.current_polygon = []
                logging.info("User chose not to save incomplete polygon.")
        elif self.canvas.current_polygon:
            # Less than 3 points, just clear
            self.canvas.current_polygon = []
            logging.info("Cleared incomplete polygon when navigating to previous image.")
        
        if self.canvas.changed:
            self.prompt_save_changes()
        # Save current selections
        self.image_selections[self.current_index] = self.selected_box_indices.copy()
        
        if self.current_index > 0:
            self.current_index -= 1
            self.logging_nav_status()
             
            # Restore selections if any
            self.selected_box_indices = set()
            if self.current_index in self.image_selections:
                self.selected_box_indices = self.image_selections[self.current_index].copy()
            else:
                 self.selected_box_indices = set()

            self.load_image()
        else:
            self.app_status_bar.set_status("Already at the first image.")

    def logging_nav_status(self):
        logging.info(f"Navigating to image index {self.current_index + 1}/{len(self.image_files)}")

    def prompt_save_changes(self):
        if not self.auto_save_cb.isChecked():
            ans = QMessageBox.question(
                self, "Save Changes?",
                "You have unsaved changes. Save before moving?",
                QMessageBox.Yes | QMessageBox.No
            )
            if ans == QMessageBox.Yes:
                self.save_annotation(auto=True)
        else:
            self.save_annotation(auto=True)

    # ----------------------------------------------------------------
    def save_annotation(self, auto=False):
        if self.mode == "view":
             if not auto:
                 QMessageBox.warning(self, "View Mode", "Cannot save modifications in View Mode.\nSwitch to Edit Mode first.")
             return
        if not self.image_files or not self.format:
            return
        img_name = self.image_files[self.current_index]
        boxes = self.canvas.boxes
        polygons = self.canvas.polygons

        if self.format == "TXT":
            os.makedirs(self.label_dir, exist_ok=True)
            # Save TXT format - convert from pixel coords to normalized
            label_file = os.path.join(self.label_dir, os.path.splitext(img_name)[0] + ".txt")
            img_h, img_w = self.canvas.image.shape[:2]
            
            with open(label_file, "w") as f:
                # 1. BBoxes (YOLO Detection)
                for box in boxes:
                    x, y, w, h, class_id = box
                    # Convert to normalized TXT format
                    xc = (x + w / 2) / img_w
                    yc = (y + h / 2) / img_h
                    bw = w / img_w
                    bh = h / img_h
                    f.write(f"{int(class_id)} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")
                
                # 2. Polygons (YOLO Segmentation)
                for pts, class_id in polygons:
                    # Format: <class-index> <x1> <y1> <x2> <y2> ... <xn> <yn> (Normalized)
                    norm_points = []
                    for (px, py) in pts:
                        norm_points.append(f"{px/img_w:.6f}")
                        norm_points.append(f"{py/img_h:.6f}")
                    points_str = " ".join(norm_points)
                    f.write(f"{int(class_id)} {points_str}\n")

        elif self.format == "JSON":
            os.makedirs(self.label_dir, exist_ok=True)
            # Pass polygons to exporter
            save_json(self.label_dir, img_name, boxes, "", polygons=polygons)
        elif self.format == "COCO":
            # Save COCO format to the specific COCO file path
            if self.coco_file_path:
                self._save_coco_annotation(img_name, boxes, polygons)
            else:
                QMessageBox.warning(self, "Error", "COCO file path not set. Cannot save.")
                logging.error("COCO file path not set. Cannot save annotation.")
                return

        self.canvas.changed = False
        self.app_status_bar.set_status(get_status_message("image_saved"))
        logging.info(f"Saved annotations for '{img_name}' ({len(boxes)} boxes, {len(polygons)} polygons) format={self.format}")
        
        # Show save confirmation popup ONLY if not already shown
        # This prevents duplicate popups when navigating after manual save
        if not hasattr(self, '_last_saved_image') or self._last_saved_image != self.current_index:
            save_msg = f"Saved {img_name}\n\nBoxes: {len(boxes)}\nPolygons: {len(polygons)}"
            self.show_temporary_message("Saved", save_msg, duration=1000)
            self._last_saved_image = self.current_index

    def show_temporary_message(self, title, message, duration=1000):
        """Show a message box that auto-closes after 'duration' ms (default 1 sec) or when user clicks OK."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setDefaultButton(QMessageBox.Ok)
        msg_box.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        # Use non-blocking show
        msg_box.show()
        
        # Center on parent
        geom = msg_box.geometry()
        p_geom = self.geometry()
        x = p_geom.x() + (p_geom.width() - geom.width()) // 2
        y = p_geom.y() + (p_geom.height() - geom.height()) // 2
        msg_box.move(x, y)
        
        # Auto-close after duration (only if still visible)
        def close_msg():
            try:
                if msg_box.isVisible():
                    msg_box.close()
                    msg_box.deleteLater()
            except:
                pass
        
        QTimer.singleShot(duration, close_msg)

    def _save_coco_annotation(self, img_name, boxes, polygons=None):
        """Save annotations to COCO file at self.coco_file_path."""
        try:
            # Read existing COCO file
            if os.path.exists(self.coco_file_path):
                with open(self.coco_file_path, 'r') as f:
                    coco = json.load(f)
            else:
                # Create new COCO structure
                coco = {
                    "info": {"description": "COCO dataset created by Universal Annotator"},
                    "licenses": [],
                    "images": [],
                    "annotations": [],
                    "categories": []
                }
            
            # Find image_id for current image
            image_id = None
            for img in coco.get("images", []):
                if img["file_name"] == img_name:
                    image_id = img["id"]
                    break
            
            if image_id is None:
                logging.warning(f"Image '{img_name}' not found in COCO file. Cannot save.")
                return
            
            # Remove existing annotations for this image
            coco["annotations"] = [ann for ann in coco.get("annotations", []) if ann.get("image_id") != image_id]
            
            # Generate new IDs
            start_id = 900000 + image_id * 1000
            if coco["annotations"]:
                 max_id = max(ann.get("id", 0) for ann in coco["annotations"])
                 start_id = max_id + 1

            # BBoxes
            for idx, (x, y, w, h, class_id) in enumerate(boxes):
                ann = {
                    "id": start_id + idx,
                    "image_id": image_id,
                    "category_id": int(class_id),
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "area": int(w * h),
                    "iscrowd": 0,
                    "segmentation": [] 
                }
                coco["annotations"].append(ann)

            # Polygons
            if polygons:
                 base_id = start_id + len(boxes)
                 for idx, (points, class_id) in enumerate(polygons):
                      # COCO Segmentation: [x1, y1, x2, y2, ...]
                      flat_points = [coord for pt in points for coord in pt]
                      
                      # Calculate bbox form polygon
                      if not points: continue
                      xs = [p[0] for p in points]
                      ys = [p[1] for p in points]
                      px, py = min(xs), min(ys)
                      pw, ph = max(xs) - px, max(ys) - py
                      
                      ann = {
                        "id": base_id + idx,
                        "image_id": image_id,
                        "category_id": int(class_id),
                        "bbox": [int(px), int(py), int(pw), int(ph)],
                        "area": int(pw * ph), 
                        "iscrowd": 0,
                        "segmentation": [flat_points] 
                      }
                      coco["annotations"].append(ann)
            
            with open(self.coco_file_path, 'w') as f:
                json.dump(coco, f, indent=2)
                
            logging.info(f"Updated COCO file '{self.coco_file_path}' for image '{img_name}'")
        
        except Exception as e:
            logging.error(f"Error saving COCO annotation: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save COCO annotation:\n{str(e)}")

    # ----------------------------------------------------------------
    def convert_annotations_to_json(self):
        """Convert all TXT (.txt) annotations in label_dir to JSON format"""
        if not self.label_dir or not os.path.exists(self.label_dir):
            msg = "Please load a dataset first."
            QMessageBox.warning(self, "No Label Dir", msg)
            logging.warning(f"TXT to JSON conversion failed: {msg}")
            return
        
        # Check if there are any .txt files
        txt_files = [f for f in os.listdir(self.label_dir) if f.endswith(".txt")]
        if not txt_files:
            msg = "No .txt files found in label directory."
            QMessageBox.warning(self, "No TXT Files", msg)
            logging.warning(f"TXT to JSON conversion failed: {msg}")
            return
        
        try:
            # Use default output folder (converted_json)
            # Pass class names so converter writes proper names instead of class_0
            class_names = self.class_manager.get_classes() if hasattr(self, 'class_manager') else None
            converted_files = convert_txt_to_json(self.label_dir, output_dir=None, img_size=None, class_names=class_names)
            output_dir = os.path.join(self.label_dir, "converted_json")
            logging.info(f"Converted {len(converted_files)} TXT files to JSON in '{output_dir}'.")
            
            QMessageBox.information(
                self, 
                "Conversion Complete", 
                f"Successfully converted {len(converted_files)} files to JSON format.\n\n"
                f"Output: {output_dir}"
            )
            self.app_status_bar.set_status(f"Converted {len(converted_files)} files to JSON")
        except Exception as e:
            msg = f"Failed to convert TXT to JSON: {str(e)}"
            logging.error(msg)
            QMessageBox.critical(self, "Conversion Error", msg)
            self.app_status_bar.set_status("Conversion failed.")

    def convert_annotations_to_txt(self):
        """Convert all JSON annotations in label_dir to TXT (.txt) format"""
        if not self.label_dir or not os.path.exists(self.label_dir):
            msg = "Please load a dataset first."
            QMessageBox.warning(self, "No Label Dir", msg)
            logging.warning(f"JSON to TXT conversion failed: {msg}")
            return
        
        # Check if there are any .json files
        json_files = [f for f in os.listdir(self.label_dir) if f.endswith(".json")]
        if not json_files:
            msg = "No .json files found in label directory."
            QMessageBox.warning(self, "No JSON Files", msg)
            logging.warning(f"JSON to TXT conversion failed: {msg}")
            return
        
        try:
            # Discover classes in JSON files
            discovered = self._discover_classes_in_json_folder(self.label_dir)

            # If no classes discovered, prompt and abort conversion
            if not discovered:
                msg = "No class names discovered in JSON files. Please ensure your JSONs contain 'className' or 'category_name'."
                logging.warning(msg)
                QMessageBox.warning(self, "No Classes Found", msg)
                return

            # Build a simple mapping dialog where user assigns integer ids 0..n-1
            n = len(discovered)
            dlg = QDialog(self)
            dlg.setWindowTitle("Map class names to numeric IDs")

            layout = QFormLayout(dlg)
            edits = {}
            for i, name in enumerate(discovered):
                le = QLineEdit(str(i))
                le.setPlaceholderText(f"0..{n-1}")
                layout.addRow(f"{name}", le)
                edits[name] = le

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            layout.addRow(buttons)
            buttons.accepted.connect(dlg.accept)
            buttons.rejected.connect(dlg.reject)

            if dlg.exec_() != QDialog.Accepted:
                self.app_status_bar.set_status("Conversion cancelled by user.")
                return

            # Validate mappings
            mapping = {}
            used_ids = set()
            valid = True
            for name, le in edits.items():
                txt = le.text().strip()
                try:
                    val = int(txt)
                except Exception:
                    QMessageBox.warning(self, "Invalid Mapping", f"Invalid id for '{name}': '{txt}'")
                    return
                if val < 0 or val >= n:
                    QMessageBox.warning(self, "Invalid Mapping", f"ID for '{name}' must be between 0 and {n-1}.")
                    return
                if val in used_ids:
                    QMessageBox.warning(self, "Invalid Mapping", f"Duplicate ID {val} assigned. IDs must be unique.")
                    return
                used_ids.add(val)
                mapping[name] = val

            # Now call converter with mapping (non-interactive)
            convert_json_to_txt(self.label_dir, output_dir=None, image_dir=self.image_dir, class_map=mapping, interactive=False)
            output_dir = os.path.join(self.label_dir, "converted_txt")
            num_json = len(json_files)
            logging.info(f"Converted {num_json} JSON files to TXT in '{output_dir}' with user mapping.")
            QMessageBox.information(self, "Conversion Complete", f"Successfully converted {num_json} files to TXT format.\n\nOutput: {output_dir}")
            self.app_status_bar.set_status(f"Converted {num_json} files to TXT (.txt)")
        except Exception as e:
            msg = f"Failed to convert JSON to TXT: {str(e)}"
            logging.error(msg)
            QMessageBox.critical(self, "Conversion Error", msg)
            self.app_status_bar.set_status("Conversion failed.")

    def convert_annotations_to_coco(self):
        """Convert TXT annotations to COCO JSON format for RFDETR"""
        if not self.label_dir or not os.path.exists(self.label_dir):
            msg = "Please load a dataset first."
            QMessageBox.warning(self, "No Label Dir", msg)
            logging.warning(f"TXT to COCO conversion failed: {msg}")
            return
        
        if not self.image_dir or not os.path.exists(self.image_dir):
            msg = "Image directory not found."
            QMessageBox.warning(self, "No Image Dir", msg)
            logging.warning(f"TXT to COCO conversion failed: {msg}")
            return
        
        # Check if there are any .txt files
        txt_files = [f for f in os.listdir(self.label_dir) if f.endswith(".txt")]
        if not txt_files:
            msg = "No .txt files found in label directory."
            QMessageBox.warning(self, "No TXT Files", msg)
            logging.warning(f"TXT to COCO conversion failed: {msg}")
            return
        
        try:
            # Get class names
            classes = self.class_manager.get_classes()
            
            # Use default output path (converted_coco_json)
            result = convert_txt_to_coco(self.image_dir, self.label_dir, output_path=None, class_names=classes)
            
            output_path = os.path.join(self.label_dir, "converted_coco_json", "_annotations.coco.json")
            num_images = result.get("valid_images", 0)
            num_annotations = result.get("annotations", 0)
            
            QMessageBox.information(
                self,
                "Conversion Complete",
                f"Successfully converted {num_images} images with {num_annotations} annotations to COCO format.\n\n"
                f"Output: {output_path}"
            )
            self.app_status_bar.set_status(f"Converted {num_images} images to COCO JSON")
        except Exception as e:
            msg = f"Failed to convert to COCO: {str(e)}"
            logging.error(msg)
            QMessageBox.critical(self, "Conversion Error", msg)
            self.app_status_bar.set_status("Conversion failed.")

    def merge_json_to_coco_json(self):
        """Merge multiple per-image JSON files into a single COCO JSON file"""
        # Ask user to select image folder
        images_folder = QFileDialog.getExistingDirectory(self, "Select Images Folder")
        if not images_folder:
            return
        
        # Ask user to select the JSON file (or folder with JSONs)
        json_source = QFileDialog.getExistingDirectory(self, "Select Folder Containing JSON Annotation Files")
        if not json_source:
            return
        
        # Check if there are any JSON files
        json_files = [f for f in os.listdir(json_source) if f.endswith(".json") and not f.startswith("_")]
        if not json_files:
            msg = "No JSON files found in selected folder.\n\nMake sure you have per-image JSON annotation files."
            QMessageBox.warning(self, "No JSON Files", msg)
            logging.warning(f"JSON to COCO merge failed: {msg}")
            return
        
        try:
            # Get class names for categories
            classes = self.class_manager.get_classes()
            
            # Use default output path (converted_coco_json)
            result = convert_json_folder_to_coco(json_source, images_folder, output_path=None, class_names=classes)
            
            output_path = os.path.join(json_source, "converted_coco_json", "_annotations.coco.json")
            logging.info(f"Successfully merged {result['images']} images with {result['annotations']} annotations to '{output_path}'.")
            
            QMessageBox.information(
                self,
                "Merge Complete",
                f"Successfully merged {result['images']} images with {result['annotations']} annotations "
                f"into COCO format.\n\n"
                f"Classes: {result['categories']}\n\n"
                f"Output: {output_path}"
            )
            self.app_status_bar.set_status(f"Merged {result['images']} images into COCO JSON")
        except Exception as e:
            msg = f"Failed to merge JSON files: {str(e)}"
            logging.error(msg)
            QMessageBox.critical(self, "Merge Error", msg)
            self.app_status_bar.set_status("Merge failed.")

    def convert_coco_to_per_image_json(self):
        """Converts a single COCO JSON file to multiple per-image JSON files."""
        # Ask user to select the COCO JSON file
        coco_path, _ = QFileDialog.getOpenFileName(self, "Select COCO Annotation File", os.getcwd(), "COCO JSON (*.json)")
        if not coco_path:
            self.app_status_bar.set_status("Conversion cancelled.")
            return

        try:
            # Use default output folders (converted_json and classes.txt in output folder)
            convert_coco_to_json_folder(coco_path, output_json_folder=None, class_txt_path=None)
            
            output_dir = os.path.join(os.path.dirname(coco_path), "converted_json")
            
            QMessageBox.information(
                self,
                "Conversion Complete",
                f"Successfully converted COCO file to per-image JSON files.\n\n"
                f"Output folder: {output_dir}"
            )
            self.app_status_bar.set_status("Converted COCO to per-image JSONs.")
        except Exception as e:
            msg = f"Failed to convert COCO to JSONs: {str(e)}"
            logging.error(msg)
            QMessageBox.critical(self, "Conversion Error", msg)
            self.app_status_bar.set_status("Conversion failed.")

    def convert_coco_to_txt(self):
        """Converts a single COCO JSON file to multiple txt .txt files."""
        # Ask user to select the COCO JSON file
        coco_path, _ = QFileDialog.getOpenFileName(self, "Select COCO Annotation File", os.getcwd(), "COCO JSON (*.json)")
        if not coco_path:
            self.app_status_bar.set_status("Conversion cancelled.")
            return

        try:
            # Use default output folders (converted_txt and classes.txt in output folder)
            convert_coco_to_txt(coco_path, output_txt_folder=None, classes_txt_path=None)
            
            output_dir = os.path.join(os.path.dirname(coco_path), "converted_txt")
            
            QMessageBox.information(
                self,
                "Conversion Complete",
                f"Successfully converted COCO file to txt .txt files.\n\n"
                f"Output folder: {output_dir}"
            )
            self.app_status_bar.set_status("Converted COCO to txt TXTs.")
        except Exception as e:
            msg = f"Failed to convert COCO to TXTs: {str(e)}"
            logging.error(msg)
            QMessageBox.critical(self, "Conversion Error", msg)
            self.app_status_bar.set_status("Conversion failed.")

    def keyPressEvent(self, event):
        """Handle global key events."""
        if event.key() == Qt.Key_Escape:
             # Always treat Escape as Quit/Close request - use prompt!
             self.close_prompt()
             return
        
        # Explicitly handle V for View Mode and E for Edit Mode to ensure reliability
        if event.key() == Qt.Key_V:
            self.set_view_mode()
            return
        
        if event.key() == Qt.Key_E:
            self.set_edit_mode()
            return
            
        super().keyPressEvent(event)