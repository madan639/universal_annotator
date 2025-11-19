import os
import json
import logging
import re
from PyQt5.QtWidgets import ( 
    QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QFileDialog, QApplication,
    QMessageBox, QCheckBox, QSizePolicy, QListWidgetItem, QDialog, QLabel,
    QTextEdit, QPushButton, QProgressDialog
)
from PyQt5.QtCore import Qt
from .canvas_widget import CanvasWidget
from .class_manager import ClassManager
from exporters.json_exporter import save_json
from exporters.coco_exporter import save_coco
from utils.file_utils import list_images
from ui.themes import ThemeManager 
from ui.components import LabelPanel, ControlPanel, LabelListItemWidget
from ui.dialogs import ClassSelectionDialog, HelpDialog, AboutDialog, ClassManagementDialog 
from ui.menus import AppMenuBar
from ui.statusbar import AppStatusBar
from ui.messages import get_tooltip, get_status_message
from converters.txt_to_json_converter import convert_txt_to_json
from converters.json_to_txt import convert_json_to_txt
from converters.txt_to_annotaion_coco_json import convert_txt_to_coco
from converters.json_to_coco_merge import convert_json_folder_to_coco
from converters.coco_to_json_converter import convert_coco_to_json_folder
from converters.coco_to_txt_converter import convert_coco_to_txt



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

        # --- State ---
        self.image_dir = None
        self.label_dir = None
        self.coco_file_path = None  # Path to COCO annotation file
        self.format = "TXT"  # Default format is TXT
        self.mode = "view"
        self.image_files = []
        self.current_index = 0
        self.class_manager = ClassManager(os.path.join(os.getcwd(), "sample_classes", "classes.txt"))
        self.selected_box_indices = set()  # Track which boxes are selected

        # --- Per-image selection memory ---
        self.image_selections = {}  # Dict: image_index -> set of selected box indices
        self.manual_deselect_all = False  # Track if user clicked "Deselect All"

        # --- Status Bar (must be created before canvas to connect signals) ---
        self.app_status_bar = AppStatusBar(self)
        self.setStatusBar(self.app_status_bar)

        # --- Canvas ---
        self.canvas = CanvasWidget(self, mode=self.mode, classes=self.class_manager.get_classes())
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.box_added.connect(self.on_box_added)  # Connect to box added signal
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

        # --- Status Label ---
        self.status_label = QLabel("View Mode (Read Only)")
        self.status_label.setStyleSheet("padding: 8px; font-weight: bold;")

        # --- Layout ---
        # Left sidebar: Controls
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.control_panel)
        left_layout.addWidget(self.auto_save_cb)
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
        
        # Get a sorted list of indices to delete, in reverse order to avoid index shifting issues
        indices_to_delete = sorted(list(self.selected_box_indices), reverse=True)
        
        logging.info(f"Image '{img_name}': Deleting {len(indices_to_delete)} selected boxes with indices: {indices_to_delete}")

        # Remove the boxes from the canvas list
        for index in indices_to_delete:
            if 0 <= index < len(self.canvas.boxes):
                self.canvas.boxes.pop(index)
        
        # --- State update ---
        # Re-index selected boxes after multiple deletions
        self._reindex_selections_after_multiple_deletions(indices_to_delete)
        
        # Mark canvas as changed
        self.canvas.changed = True
        
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
            self.image_selections = {}
            
            self._create_initial_files()
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
            self.image_selections = {}
            
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
                    from PIL import Image
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
            self.image_selections = {}
            self.coco_file_path = coco_file_path
            
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
            self.image_selections = {}
            self.coco_file_path = coco_path
            
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
        self.coco_file_path = None  # Reset COCO file path
        # Controls whether per-image JSON textual names are used for label display.
        # Default: do NOT show JSON-derived per-box names until the user confirms
        # discovered classes or manually provides classes.
        self.json_display_override = False

        # Load classes respecting precedence:
        # 1) If classes already set in this session (e.g., user manually entered), keep them.
        # 2) Else if user_classes/classes.txt exists, load it.
        # 3) Else fall back to sample_classes/classes.txt if present.
        try:
            current = []
            try:
                current = self.class_manager.get_classes() or []
            except Exception:
                current = getattr(self.class_manager, 'classes', []) or []

            if current:
                # session-provided classes exist — preserve them
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
                        logging.debug("Failed to load user_classes/classes.txt; falling back to sample if available")
                elif os.path.exists(sample_path):
                    try:
                        self.class_manager.set_classes_file(sample_path)
                        logging.info(f"Loaded classes from sample_classes: {sample_path}")
                    except Exception:
                        logging.debug("Failed to load sample_classes/classes.txt; continuing with empty classes list")
                else:
                    # No classes file found; ensure attribute exists
                    if not hasattr(self.class_manager, 'classes'):
                        self.class_manager.classes = []
        except Exception:
            # Preserve stability: ensure classes list exists
            try:
                self.class_manager.classes = self.class_manager.get_classes() or []
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
        
        # Suggest labels folder in same parent directory as images
        img_parent = os.path.dirname(img_dir.rstrip('/\\'))
        img_basename = os.path.basename(img_dir.rstrip('/\\'))
        suggested_lbl_dir = os.path.join(img_parent, 'labels')
        
        # Check if labels folder already exists
        folder_exists = os.path.isdir(suggested_lbl_dir)
        
        # Ask user: Create new labels folder or select existing
        if folder_exists:
            msg = (f"Image folder: {img_dir}\n\n"
                   f"Labels folder already exists at: {suggested_lbl_dir}\n\n"
                   f"Would you like to:\n"
                   f"- YES: Use existing labels folder at {suggested_lbl_dir}\n"
                   f"- NO: Select a different labels folder manually")
        else:
            msg = (f"Image folder: {img_dir}\n\n"
                   f"Suggested labels folder: {suggested_lbl_dir}\n\n"
                   f"Would you like to:\n"
                   f"- YES: Create new labels folder at {suggested_lbl_dir}\n"
                   f"- NO: Select existing labels folder manually")
        
        reply = QMessageBox.question(
            self, "Labels Folder",
            msg,
            QMessageBox.Yes | QMessageBox.No
        )
        
        created_new_folder = False
        if reply == QMessageBox.Yes:
            if folder_exists:
                # Folder already exists, use it
                lbl_dir = suggested_lbl_dir
                logging.info(f"Using existing labels folder: {lbl_dir}")
            else:
                # Create new labels folder
                try:
                    os.makedirs(suggested_lbl_dir, exist_ok=True)
                    lbl_dir = suggested_lbl_dir
                    created_new_folder = True
                    logging.info(f"Created labels folder: {lbl_dir}")
                    QMessageBox.information(self, "Labels Folder Created", 
                        f"✓ Labels folder created successfully at:\n{lbl_dir}\n\nTXT files will be created for your images.")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to create labels folder:\n{str(e)}")
                    logging.error(f"Failed to create labels folder: {e}")
                    return
        else:
            # User selects different folder
            lbl_dir = QFileDialog.getExistingDirectory(self, "Select Label Folder")
            if not lbl_dir:
                return
            logging.info(f"User selected labels folder: {lbl_dir}")

        self.image_dir, self.label_dir = img_dir, lbl_dir
        self.image_files = list_images(img_dir)
        if not self.image_files:
            msg = "No image files found in the folder."
            QMessageBox.warning(self, "No Images", msg)
            logging.warning(f"{msg} Path: {img_dir}")
            self.app_status_bar.set_status(get_status_message("no_images"))
            return

        # Sort image files using natural/numeric sorting
        # This ensures 6f.jpg comes before 1108f.jpg
        self.image_files.sort(key=natural_sort_key)

        # If we created a new folder, create TXT files by default (no dialog)
        if created_new_folder:
            self.format = "TXT"
            logging.info("New folder created. Using TXT format by default.")
            # Create initial annotation files
            self._create_initial_files()
        else:
            # If caller provided a preferred format (user explicitly selected), honor it
            if prefer_format:
                self.format = prefer_format
                logging.info(f"Using preferred annotation format: {prefer_format}")
            else:
                # Auto-detect format from label files
                detected_format = self._detect_format()
                if detected_format:
                    self.format = detected_format
                    logging.info(f"Auto-detected annotation format: {detected_format}")
                else:
                    logging.warning("Could not auto-detect format. Prompting user.")
                    QMessageBox.warning(
                        self, "No Labels Found",
                        "No annotation files detected in the label folder.\n"
                        "Please select a format manually."
                    )
                    self.select_format()
                    if not self.format:
                        # If user cancels format selection after auto-detection fails,
                        # we should clear the image files and reset state.
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
                        return

        # Load first image and its labels automatically
        self.current_index = 0
        self.selected_box_indices = set()
        self.image_selections = {}  # IMPORTANT: Reset per-image selections for new dataset
        self._update_format_display()

        # If no classes are loaded and format is TXT or JSON, prompt user to enter classes
        # Show the new integrated class management dialog
        # If format is JSON, attempt to discover classes in the label folder and prompt
        if self.format == 'JSON':
            try:
                # Estimate sample scan time and show a small progress dialog so the
                # user knows the app is working and gets an estimate.
                files = []
                if os.path.isdir(self.label_dir):
                    for fn in os.listdir(self.label_dir):
                        if fn.endswith('.json'):
                            files.append(fn)
                sample_count = min(len(files), 20)
                est_secs = max(0.2, sample_count * 0.02)
                pd = QProgressDialog(f"Scanning {sample_count} JSON files (est. {est_secs:.1f}s)...", None, 0, 0, self)
                pd.setWindowTitle("Inspecting JSON dataset")
                pd.setWindowModality(Qt.WindowModal)
                pd.setAutoClose(True)
                pd.show()
                QApplication.processEvents()

                # Detect which JSON keys most likely contain textual class names
                try:
                    self.json_name_keys = self._detect_json_name_keys(self.label_dir)
                except Exception:
                    self.json_name_keys = ['className', 'category_name', 'name', 'label']

                # detect bbox style for this JSON dataset so extraction is dynamic
                try:
                    self.json_bbox_methods = self._detect_json_bbox_style(self.label_dir)
                except Exception:
                    self.json_bbox_methods = ['contour', 'bbox', 'points', 'xywh']

                # Discover classes (for user confirmation)
                discovered = self._discover_classes_in_json_folder(self.label_dir)

                # Close progress dialog and continue
                try:
                    pd.close()
                except Exception:
                    pass

            except Exception as e:
                logging.debug(f"JSON detection progress dialog failed: {e}")
                # fallback to direct discovery
                try:
                    self.json_name_keys = self._detect_json_name_keys(self.label_dir)
                except Exception:
                    self.json_name_keys = ['className', 'category_name', 'name', 'label']
                try:
                    self.json_bbox_methods = self._detect_json_bbox_style(self.label_dir)
                except Exception:
                    self.json_bbox_methods = ['contour', 'bbox', 'points', 'xywh']
                discovered = self._discover_classes_in_json_folder(self.label_dir)

            # If discovered, prompt the user to confirm/edit the discovered classes
            if discovered:
                # show the editable confirmation dialog so user can accept / change mapping
                if not self._prompt_use_discovered_json_classes(discovered):
                    # user cancelled: fall back to manual class dialog
                    self._show_class_management_dialog()
                else:
                    # User confirmed discovered classes — enable JSON-derived display
                    self.json_display_override = True
            else:
                # fallback to manual dialog if nothing discovered
                self._show_class_management_dialog()
        else:
            self._show_class_management_dialog()
        
        self.load_image()
        self.app_status_bar.set_status(get_status_message("dataset_loaded"))
        logging.info(f"Dataset loaded. Images: {len(self.image_files)}. Format: {self.format}.")

        # Populate the image jump box
        self._populate_image_jump_box()

    def _populate_image_jump_box(self):
        """Fills the image jump dropdown with the names of loaded images."""
        self.image_jump_box.blockSignals(True)
        self.image_jump_box.clear()
        items = [f"{i+1}: {os.path.basename(name)}" for i, name in enumerate(self.image_files)]
        self.image_jump_box.addItems(items)
        self.image_jump_box.blockSignals(False)

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
        """Scan a folder (or single JSON file) and discover unique class names.

        Returns an ordered list of discovered names (may be empty).
        """
        discovered = []
        if not folder_path:
            return discovered

        counts = {}
        files = []
        try:
            if os.path.isdir(folder_path):
                for fn in os.listdir(folder_path):
                    if fn.endswith('.json'):
                        files.append(os.path.join(folder_path, fn))
            else:
                files = [folder_path]
        except Exception:
            return discovered

        # Candidate keys to check beyond the auto-detected ones
        extra_keys = ['class', 'className','trackName', 'trackname', 'labelText', 'label', 'objectClass', 'tag']

        def add_count(name):
            if not name or not isinstance(name, str):
                return
            s = name.strip()
            if not s:
                return
            if self._looks_like_id(s):
                return
            counts[s] = counts.get(s, 0) + 1

        for p in files:
            try:
                with open(p, 'r') as f:
                    d = json.load(f)
            except Exception:
                continue

            # if COCO categories present, persist id->name map and also count those names
            if isinstance(d, dict) and isinstance(d.get('categories'), list):
                try:
                    coco_map = getattr(self, 'json_coco_category_map', {}) or {}
                    for cat in d.get('categories', []):
                        if isinstance(cat, dict):
                            name = cat.get('name') or cat.get('label')
                            add_count(name)
                            cid = cat.get('id') or cat.get('category_id')
                            if cid is not None:
                                try:
                                    coco_map[int(cid)] = name
                                except Exception:
                                    pass
                    if coco_map:
                        setattr(self, 'json_coco_category_map', coco_map)
                except Exception:
                    pass

            # unify objects extraction for dicts and lists
            obj_lists = []
            if isinstance(d, dict):
                if isinstance(d.get('objects'), list):
                    obj_lists.append(d.get('objects'))
                if isinstance(d.get('annotations'), list):
                    obj_lists.append(d.get('annotations'))
                # some datasets use top-level 'frames' with nested objects
                if isinstance(d.get('frames'), list):
                    for fr in d.get('frames'):
                        if isinstance(fr, dict):
                            if isinstance(fr.get('objects'), list):
                                obj_lists.append(fr.get('objects'))
            elif isinstance(d, list):
                for el in d:
                    if isinstance(el, dict):
                        if isinstance(el.get('objects'), list):
                            obj_lists.append(el.get('objects'))
                        if isinstance(el.get('annotations'), list):
                            obj_lists.append(el.get('annotations'))

            # Inspect found object lists
            for objs in obj_lists:
                for o in objs:
                    if not isinstance(o, dict):
                        continue
                    # Use the robust extractor to get likely name
                    try:
                        nm = self._get_name_from_object(o)
                        if nm:
                            add_count(nm)
                            continue
                    except Exception:
                        pass

                    # fallback: check a few extra keys directly
                    for k in extra_keys:
                        v = o.get(k)
                        if isinstance(v, str) and v.strip() and not self._looks_like_id(v):
                            add_count(v.strip())
                            break

                    # last resort: if category is dict or string
                    cat = o.get('category')
                    if isinstance(cat, dict):
                        nm = cat.get('name') or cat.get('label')
                        if isinstance(nm, str) and nm.strip():
                            add_count(nm.strip())
                    elif isinstance(cat, str) and cat.strip() and not self._looks_like_id(cat):
                        add_count(cat.strip())

        # Build ordered list by frequency
        ordered = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        names = [k for k, v in ordered if k]

        # Filter out generic geometric tokens if more informative names exist
        generic_tokens = { 'rectangle', 'rect', 'box', 'bbox', 'region', 'shape' }
        filtered = [n for n in names if n.lower() not in generic_tokens]
        if filtered:
            names = filtered

        # Deduplicate maintaining order, prefer most frequent variant (normalize by label)
        seen_norm = set()
        discovered = []
        for n in names:
            norm = self._normalize_label(n) or n.strip().lower()
            if norm in seen_norm:
                # already have a variant for this normalized token; skip
                continue
            seen_norm.add(norm)
            discovered.append(n)

        # If nothing discovered, emit diagnostics for a few sample files
        if not discovered:
            try:
                sample_paths = files[:3]
                logging.info(f"_discover_classes_in_json_folder: inspected {len(sample_paths)} sample files, no class names found.")
                for p in sample_paths:
                    try:
                        with open(p, 'r') as f:
                            d = json.load(f)
                    except Exception as e:
                        logging.debug(f"_discover_classes_in_json_folder: failed to read sample {p}: {e}")
                        continue
                    if isinstance(d, dict):
                        logging.info(f"Sample JSON keys for '{os.path.basename(p)}': {list(d.keys())}")
                        objs = d.get('objects') or d.get('annotations') or d.get('frames') or []
                        if isinstance(objs, list) and objs:
                            first = objs[0]
                            if isinstance(first, dict):
                                logging.info(f"Sample object keys: {list(first.keys())}")
                                preview_keys = [k for k in first.keys()][:8]
                                for k in preview_keys:
                                    logging.info(f"  {k}: {repr(first.get(k))}")
                    elif isinstance(d, list):
                        logging.info(f"Sample JSON (list) length for '{os.path.basename(p)}': {len(d)}")
                        if d and isinstance(d[0], dict):
                            logging.info(f"Sample element keys: {list(d[0].keys())}")
            except Exception as e:
                logging.debug(f"_discover_classes_in_json_folder diagnostics failed: {e}")

        return discovered

    def _detect_json_bbox_style(self, folder_path, sample_limit=20):
        """Inspect a few JSON files and return a prioritized list of bbox styles found.

        Returns a list like ['contour','bbox','points','xywh'] ordered by frequency.
        """
        counts = {'contour': 0, 'bbox': 0, 'points': 0, 'xywh': 0}
        try:
            files = []
            if os.path.isdir(folder_path):
                for fn in os.listdir(folder_path):
                    if fn.endswith('.json'):
                        files.append(os.path.join(folder_path, fn))
                        if len(files) >= sample_limit:
                            break
            else:
                files = [folder_path]

            def inspect_obj(o):
                if not isinstance(o, dict):
                    return
                if 'contour' in o and isinstance(o.get('contour'), dict) and isinstance(o['contour'].get('points'), list):
                    counts['contour'] += 1
                if 'bbox' in o and isinstance(o.get('bbox'), (list, tuple)) and len(o.get('bbox', [])) == 4:
                    counts['bbox'] += 1
                if 'points' in o and isinstance(o.get('points'), list) and len(o.get('points')) >= 2:
                    counts['points'] += 1
                if 'x' in o and 'y' in o and ('w' in o or 'width' in o or 'height' in o):
                    counts['xywh'] += 1

            for p in files:
                try:
                    with open(p, 'r') as f:
                        d = json.load(f)
                except Exception:
                    continue

                if isinstance(d, dict):
                    # If COCO-style categories present, save map for later
                    if 'categories' in d and isinstance(d.get('categories'), list):
                        try:
                            coco_map = {}
                            for cat in d.get('categories', []):
                                if isinstance(cat, dict):
                                    cid = cat.get('id') or cat.get('category_id')
                                    name = cat.get('name') or cat.get('label')
                                    if cid is not None and name:
                                        try:
                                            coco_map[int(cid)] = name
                                        except Exception:
                                            pass
                            if coco_map:
                                setattr(self, 'json_coco_category_map', coco_map)
                        except Exception:
                            pass

                    # Inspect per-object lists
                    objs = []
                    if isinstance(d.get('objects'), list):
                        objs += d.get('objects')
                    if isinstance(d.get('annotations'), list):
                        objs += d.get('annotations')
                    for o in objs:
                        inspect_obj(o)
                elif isinstance(d, list):
                    for el in d:
                        if not isinstance(el, dict):
                            continue
                        for o in el.get('objects', []) + el.get('annotations', []):
                            inspect_obj(o)
        except Exception as e:
            logging.debug(f"_detect_json_bbox_style error: {e}")

        ordered = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        methods = [k for k, v in ordered if v > 0]
        if not methods:
            methods = ['contour', 'bbox', 'points', 'xywh']
        logging.info(f"Detected JSON bbox styles: {methods}")
        return methods

    def _detect_json_name_keys(self, folder_path, sample_limit=20):
        """Inspect sample JSON files and return ordered list of likely name keys.

        This looks for object-level keys whose values are strings (e.g. 'className', 'category_name', 'label')
        and also recognizes container keys like 'category' that contain a 'name' field (returned as 'category.name').
        """
        counts = {}
        try:
            files = []
            if os.path.isdir(folder_path):
                for fn in os.listdir(folder_path):
                    if fn.endswith('.json'):
                        files.append(os.path.join(folder_path, fn))
                        if len(files) >= sample_limit:
                            break
            else:
                files = [folder_path]

            def inspect_obj(o):
                if not isinstance(o, dict):
                    return
                for k, v in o.items():
                    # skip numeric bbox-like keys and obvious id fields
                    if k in ('bbox', 'contour', 'points', 'x', 'y', 'w', 'h', 'width', 'height'):
                        continue
                    if k.lower() in ('id', 'uuid', 'uid', 'trackid', 'instance_id', 'timestamp'):
                        continue
                    # string values are candidate name keys, but skip opaque ids (uuids)
                    if isinstance(v, str) and v.strip() and not self._looks_like_id(v):
                        counts[k] = counts.get(k, 0) + 1
                    # dict value that contains 'name' or 'label' -> 'k.name'
                    if isinstance(v, dict):
                        if 'name' in v or 'label' in v:
                            compound = f"{k}.name"
                            counts[compound] = counts.get(compound, 0) + 1

            for p in files:
                try:
                    with open(p, 'r') as f:
                        d = json.load(f)
                except Exception:
                    continue

                if isinstance(d, dict):
                    for o in d.get('objects', []) + d.get('annotations', []):
                        inspect_obj(o)
                elif isinstance(d, list):
                    for el in d:
                        if not isinstance(el, dict):
                            continue
                        for o in el.get('objects', []) + el.get('annotations', []):
                            inspect_obj(o)
        except Exception as e:
            logging.debug(f"_detect_json_name_keys error: {e}")

        ordered = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        keys = [k for k, v in ordered if v > 0]
        # Prefer keys that look like class/name/label and avoid generic tokens like 'type'
        generic_avoid = {'type', 'trackname', 'trackid', 'id', 'uuid', 'uid', 'instance_id'}
        preferred = [k for k in keys if any(substr in k.lower() for substr in ('class', 'name', 'label')) and k.lower() not in generic_avoid]
        others = [k for k in keys if k not in preferred and k.lower() not in generic_avoid]
        tail = [k for k in keys if k.lower() in generic_avoid]
        reordered = preferred + others + tail
        if not reordered:
            return ['className', 'category_name', 'name', 'label']
        logging.info(f"Detected name keys in JSON: {reordered}")
        return reordered

    # def _get_name_from_object(self, o):
    #     """Extract a human-readable class name from an annotation object if present."""
    #     if not isinstance(o, dict):
    #         return None
    #     keys_to_try = getattr(self, 'json_name_keys', None) or ('className', 'category_name', 'name', 'label')
    #     for k in keys_to_try:
    #         if isinstance(k, str) and '.' in k:
    #             top, sub = k.split('.', 1)
    #             val = o.get(top)
    #             if isinstance(val, dict):
    #                 v = val.get(sub)
    #             else:
    #                 v = None
    #         else:
    #             v = o.get(k)
    #         if isinstance(v, str) and v.strip():
    #             return v.strip()
    #     # Fallback: inspect 'category' container
    #     cat = o.get('category')
    #     if isinstance(cat, dict):
    #         nm = cat.get('name') or cat.get('label')
    #         if isinstance(nm, str) and nm.strip():
    #             return nm.strip()
    #     if isinstance(cat, str) and cat.strip():
    #         return cat.strip()
    #     # If object contains numeric category id and we have a COCO map, resolve it
    #     try:
    #         coco_map = getattr(self, 'json_coco_category_map', None)
    #         if coco_map:
    #             for id_key in ('category_id', 'classId', 'cat_id', 'category'):
    #                 if id_key in o and o.get(id_key) is not None:
    #                     try:
    #                         cid = int(o.get(id_key))
    #                         if cid in coco_map:
    #                             return coco_map[cid]
    #                     except Exception:
    #                         # category may be a string - skip here
    #                         pass
    #     except Exception:
    #         pass
    #     return None
    def _get_name_from_object(self, obj):
        """Dynamic class name extraction based on detected JSON keys."""
        if not isinstance(obj, dict):
            return None

        # Use dataset-detected keys first
        keys = getattr(self, "json_name_keys", [])
        # avoid picking generic geometry tokens like RECTANGLE from 'type'
        generic_tokens = {'rectangle', 'rect', 'box', 'bbox', 'region', 'shape'}
        for k in keys:
            # support nested "category.name" pattern
            if "." in k:
                top, sub = k.split(".", 1)
                val = obj.get(top)
                if isinstance(val, dict):
                    name = val.get(sub)
                    if isinstance(name, str) and name.strip() and not self._looks_like_id(name) and name.strip().lower() not in generic_tokens:
                        return name.strip()
            else:
                name = obj.get(k)
                if isinstance(name, str) and name.strip() and not self._looks_like_id(name) and name.strip().lower() not in generic_tokens:
                    return name.strip()
        # Fallback: check common keys (case-insensitive) and nested containers
        candidate_keys = {"classname","className","class","category_name","name","label","trackname","trackName","labeltext","object","objectclass","tag","category"}
        for k, v in obj.items():
            if not isinstance(k, str):
                continue
            if k.lower() in {ck.lower() for ck in candidate_keys}:
                if isinstance(v, str) and v.strip() and not self._looks_like_id(v):
                    # ignore generic geometry / shape tokens
                    if v.strip().lower() not in generic_tokens:
                        return v.strip()
                # If this is a dict with name/label inside
                if isinstance(v, dict):
                    nm = v.get('name') or v.get('label')
                    if isinstance(nm, str) and nm.strip() and not self._looks_like_id(nm):
                        if nm.strip().lower() not in generic_tokens:
                            return nm.strip()

        # category object last-resort
        cat = obj.get("category")
        if isinstance(cat, dict):
            nm = cat.get('name') or cat.get('label')
            if isinstance(nm, str) and nm.strip():
                return nm.strip()

        # If COCO id mapping exists, try to resolve common id keys
        try:
            coco_map = getattr(self, 'json_coco_category_map', None)
            if coco_map:
                for id_key in ('category_id', 'classId', 'cat_id', 'category'):
                    if id_key in obj and obj.get(id_key) is not None:
                        try:
                            cid = int(obj.get(id_key))
                            if cid in coco_map:
                                return coco_map[cid]
                        except Exception:
                            pass
        except Exception:
            pass

        return None


    def _normalize_label(self, name):
        """Normalize a label for fuzzy matching: lower, strip, remove punctuation, collapse spaces."""
        if not isinstance(name, str):
            return None
        s = name.strip().lower()
        # replace some common punctuation with space
        s = re.sub(r"[^a-z0-9]+", ' ', s)
        s = re.sub(r"\s+", ' ', s).strip()
        return s

    def _looks_like_id(self, s):
        """Return True if given string is likely an opaque id/uuid not a human label.

        Heuristics: UUID pattern or long hex with dashes or long length (>20) with many hex chars.
        """
        if not isinstance(s, str):
            return False
        s = s.strip()
        if not s:
            return False
        # common UUID pattern
        uuid_re = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
        if uuid_re.match(s):
            return True
        # long hex-like strings (no spaces) often are ids
        if len(s) >= 20 and re.fullmatch(r'[0-9a-fA-F\-]+', s):
            return True
        return False

    def _prompt_use_discovered_json_classes(self, discovered):
        """Show a confirmation dialog listing discovered classes and allow user to rename/confirm them."""
        if not discovered:
            return False

        # Create dialog with editable fields per discovered class
        dlg = QDialog(self)
        dlg.setWindowTitle("Discovered Classes - Confirm / Edit")
        from PyQt5.QtWidgets import QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QLabel

        vbox = QVBoxLayout(dlg)
        info = QLabel("Detected the following classes in JSON files. You can edit any name before applying:")
        vbox.addWidget(info)

        form = QFormLayout()
        edits = {}
        for name in discovered:
            le = QLineEdit(name)
            form.addRow(name, le)
            edits[name] = le

        vbox.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        vbox.addWidget(buttons)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)

        if dlg.exec_() != QDialog.Accepted:
            logging.info("User cancelled applying discovered JSON classes.")
            return False

        # Collect edited names and ensure uniqueness
        edited = []
        seen = set()
        for orig in discovered:
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

        # Apply classes for display only (do not overwrite classes.txt unless user saves)
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
                QMessageBox.information(self, "✓ Files Created", 
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
                QMessageBox.information(self, "✓ Files Created", 
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
                QMessageBox.information(self, "✓ File Created", 
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
        self.update_status_label()
        self.app_status_bar.set_mode("edit")
        self.app_status_bar.set_status("Edit Mode Enabled. Press 'M' to enter Drawing Mode, then click and drag to create boxes. Press 'X' to exit Drawing Mode.")

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

    # ----------------------------------------------------------------
    def keyPressEvent(self, e):
        key = e.key()
        if key in (Qt.Key_Q, Qt.Key_Escape):
            self.close_prompt()
        elif key == Qt.Key_A:
            logging.info(f"Key A pressed: navigating to previous image (format={self.format})")
            self.prev_image()
        elif key == Qt.Key_D:
            logging.info(f"Key D pressed: navigating to next image (format={self.format})")
            self.next_image()
        elif key == Qt.Key_Delete and self.mode == "edit":
            # Delete the currently selected boxes
            self.delete_selected_boxes()
        elif key == Qt.Key_S:
            self.save_annotation()
        elif key == Qt.Key_M and self.mode == "edit":
            # Toggle drawing mode on the canvas
            is_drawing = self.canvas.toggle_drawing_mode()
            if is_drawing:
                self.app_status_bar.set_status("Drawing mode enabled. Click and drag to create boxes.")
                self.app_status_bar.set_mode("drawing")
            else:
                self.app_status_bar.set_status("Drawing mode disabled. Back to edit mode.")
                self.app_status_bar.set_mode("edit")
        elif key == Qt.Key_X and self.mode == "edit":
            # Explicitly disable drawing mode
            if self.canvas.is_drawing_enabled:
                self.canvas.set_drawing_mode(enabled=False)
                self.app_status_bar.set_status("Drawing mode disabled. Back to edit mode.")
                self.app_status_bar.set_mode("edit")

    def close_prompt(self):
        reply = QMessageBox.question(
            self, "Exit", "Are you sure you want to quit?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.close()

    # ----------------------------------------------------------------
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
        if self.format == "TXT":
            file = os.path.join(self.label_dir, os.path.splitext(img_name)[0] + ".txt")
            if os.path.exists(file):
                boxes = self._load_txt_boxes(file, self.canvas.image.shape[:2])
        elif self.format == "JSON":
            file = os.path.join(self.label_dir, os.path.splitext(img_name)[0] + ".json")
            if os.path.exists(file):
                boxes = self._load_json_boxes(file)
            else:
                # Check in converted_json subfolder
                converted_file = os.path.join(self.label_dir, "converted_json", os.path.splitext(img_name)[0] + ".json")
                if os.path.exists(converted_file):
                    boxes = self._load_json_boxes(converted_file)
        elif self.format == "COCO":
            file = os.path.join(self.label_dir, "_annotations.coco.json")
            if os.path.exists(file):
                boxes = self._load_coco_boxes(file, img_name)

        # now push them into the canvas
        self.canvas.boxes = boxes
        # Log summary when in JSON mode so user can see what's loaded
        if self.format == "JSON":
            try:
                src = file if os.path.exists(file) else converted_file if 'converted_file' in locals() and os.path.exists(converted_file) else '<not-found>'
            except Exception:
                src = '<unknown>'
            classes = self.class_manager.get_classes()
            class_names = []
            for b in boxes:
                cid = b[4]
                name = None
                try:
                    if isinstance(cid, int) and cid < len(classes):
                        name = classes[cid]
                    else:
                        name = self._get_json_classname_for_box(img_name, b)
                except Exception:
                    name = None
                class_names.append(name or str(cid))

            logging.info(f"Loaded JSON annotations for '{img_name}' from '{src}': {len(boxes)} boxes. Sample classes: {', '.join(class_names[:10])}{'...' if len(class_names)>10 else ''}")
        self.canvas.changed = False
        self.canvas.update()
        
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
                valid_selections = {idx for idx in saved_selections if idx < len(boxes)}
                self.selected_box_indices = valid_selections
                logging.info(f"[LOAD_IMAGE] REVISITING IMAGE: Restored {len(valid_selections)}/{len(boxes)} boxes from history. selected_box_indices={self.selected_box_indices}")
            else:
                # First time visiting this image - select all boxes by default
                if self.manual_deselect_all:
                    self.selected_box_indices = set()  # Respect user's choice to deselect
                    logging.info(f"[LOAD_IMAGE] FIRST VISIT + manual_deselect_all=True: selected_box_indices={self.selected_box_indices}")
                else:
                    self.selected_box_indices = set(range(len(boxes)))  # Default to all selected
                    logging.info(f"[LOAD_IMAGE] FIRST VISIT + manual_deselect_all=False: selected_box_indices={self.selected_box_indices} (range 0-{len(boxes)-1})")
        else:
            # Selections are already set - likely pre-set by code (shouldn't normally happen)
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
    def update_labels_panel(self, boxes):
        """Update the labels list panel with all current boxes."""
        self.labels_list.blockSignals(True)  # Block signals to avoid triggering on_label_toggled
        self.labels_list.clear()

        # Get all class names
        classes = self.class_manager.get_classes()
        
        logging.info(f"[UPDATE_LABELS_PANEL] Called with {len(boxes)} boxes. Current selected_box_indices={self.selected_box_indices}")

        # Block signals from the QListWidget itself, but not from the custom widgets
        self.labels_list.blockSignals(True)

        for idx, box in enumerate(boxes):
            # box format: (x, y, w, h, cls)
            try:
                class_idx = int(box[4])
            except Exception:
                # If class is not numeric for any reason, fallback to str
                class_idx = None

            class_name = None
            reason = None
            # If JSON dataset, prefer the JSON-provided textual name when available,
            # but only if the user has confirmed discovered classes (json_display_override)
            # or if there is no viable class mapping available.
            if self.format == 'JSON':
                img_name = self.image_files[self.current_index] if self.image_files else None
                try:
                    json_name = self._get_json_classname_for_box(img_name, box)
                except Exception:
                    json_name = None
                # Only apply JSON-provided textual names when override is enabled
                # (user confirmed discovered classes) OR when numeric mapping cannot
                # resolve a human-friendly name.
                if json_name and isinstance(json_name, str) and json_name.strip():
                    apply_json_name = False
                    if getattr(self, 'json_display_override', False):
                        apply_json_name = True
                    else:
                        # If we can't map the numeric class to a known class, prefer JSON name
                        try:
                            class_idx_try = int(box[4])
                            classes = self.class_manager.get_classes()
                            if not isinstance(class_idx_try, int) or class_idx_try < 0 or class_idx_try >= len(classes):
                                apply_json_name = True
                        except Exception:
                            apply_json_name = True
                    if apply_json_name:
                        class_name = json_name.strip()
                        reason = "original JSON className preferred"
                        logging.debug(f"Label panel: box idx={idx} using JSON name='{class_name}' for display")
            # If no JSON name or not JSON format, fall back to numeric mapping
            if not class_name:
                if isinstance(class_idx, int) and class_idx < len(classes):
                    class_name = classes[class_idx]
                    reason = f"mapped via classes.txt index {class_idx}"
                    logging.debug(f"Label panel: box idx={idx} numeric class_idx={class_idx} -> class_name='{class_name}'")
            else:
                # Try to resolve a human-friendly class name from the original
                # JSON file when running in JSON mode (avoids showing 'Class 346').
                if self.format == 'JSON':
                    img_name = self.image_files[self.current_index] if self.image_files else None
                    resolved = self._get_json_classname_for_box(img_name, box)
                    if resolved:
                        class_name = resolved
                        reason = "resolved from JSON.className"
                        logging.debug(f"Label panel: box idx={idx} resolved name from JSON='{resolved}'")

            # Fallback label
            if not class_name:
                if isinstance(class_idx, int):
                    class_name = classes[class_idx] if class_idx is not None and class_idx < len(classes) else f"Class {class_idx if class_idx is not None else '0'}"
                    reason = reason or "fallback to classes/class-index or Class N"
                else:
                    class_name = str(box[4])
                    reason = reason or "fallback to raw box value"

            # Emit an INFO log per label in JSON mode so user can see why this label text was chosen
            if self.format == 'JSON':
                try:
                    logging.info(f"Label[{idx}] -> display='{class_name}' (box={box[:4]}, source_reason={reason})")
                except Exception:
                    logging.info(f"Label[{idx}] -> display='{class_name}' (box index={idx})")
            
            is_checked = idx in self.selected_box_indices
            
            # Create a QListWidgetItem as a container
            item = QListWidgetItem()
            
            # Create the custom widget for the item
            widget = LabelListItemWidget(idx, class_name, is_checked, self.labels_list)
            
            # Connect signals from the custom widget
            widget.selection_toggled.connect(self.on_label_toggled_from_widget)
            widget.delete_requested.connect(self.delete_specific_box)
            widget.label_clicked.connect(self.on_label_clicked_from_widget)
            
            # Set the item's size hint to match the widget's size
            item.setSizeHint(widget.sizeHint())
            
            self.labels_list.addItem(item)
            # Ensure the QListWidgetItem carries the box index so other flows
            # (select_all / deselect_all) can reliably read it.
            try:
                item.setData(Qt.UserRole, idx)
            except Exception:
                pass
            self.labels_list.setItemWidget(item, widget)

        self.labels_list.blockSignals(False) # Unblock signals
        
        # Update canvas with VALID selections
        # This ensures bboxes appear on the image
        logging.debug(f"Setting canvas.selected_boxes to {self.selected_box_indices}")
        self.canvas.selected_boxes = self.selected_box_indices
        self.canvas.update()
    
    def on_label_toggled_from_widget(self, box_idx, is_checked):
        """Handle label checkbox toggle from the custom widget."""
        if is_checked:
            self.selected_box_indices.add(box_idx)
        else:
            self.selected_box_indices.discard(box_idx)
        self._update_selection_state(box_idx, is_checked)

    def on_label_clicked_from_widget(self, box_idx, event):
        """
        Handles a click on the label text within the custom list item widget.
        Performs single selection or toggles if Ctrl is held.
        """
        logging.debug(f"Label text for box {box_idx} clicked. Ctrl held: {event.modifiers() & Qt.ControlModifier}")

        if event.modifiers() & Qt.ControlModifier:
            # If Ctrl is held, toggle the selection state of this specific box
            is_currently_checked = box_idx in self.selected_box_indices
            self._update_selection_state(box_idx, not is_currently_checked)
        else:
            # If no modifier, select ONLY this box
            self.selected_box_indices = {box_idx}
            self.update_labels_panel(self.canvas.boxes) # Refresh to show only this one selected

        self.image_selections[self.current_index] = self.selected_box_indices.copy()

    def _update_selection_state(self, box_idx, is_checked):
        """Helper to update selected_box_indices and canvas selection."""
        if is_checked:
            self.selected_box_indices.add(box_idx)
            # If user manually selects an item after deselecting all, reset the flag
            if self.manual_deselect_all:
                self.manual_deselect_all = False
        else:
            self.selected_box_indices.discard(box_idx)
        
        # Tell canvas which boxes to highlight
        self.canvas.selected_boxes = self.selected_box_indices
        self.canvas.update()
        
        # Persist the selection state for the current image
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
    def _load_txt_boxes(self, file_path, img_shape):
        """Load TXT labels (normalized coords)."""
        img_h, img_w = img_shape
        boxes = []
        with open(file_path, "r") as f:
            for line in f:
                vals = line.strip().split()
                if len(vals) < 5:
                    continue
                cls = int(vals[0])
                xc, yc, bw, bh = map(float, vals[1:5])
                # convert from normalized to pixel coordinates
                x = (xc - bw / 2) * img_w
                y = (yc - bh / 2) * img_h
                w = bw * img_w
                h = bh * img_h
                boxes.append((x, y, w, h, cls))
        return boxes

    def _load_json_boxes(self, file_path):
        """
        Universal JSON loader — supports:
        - dict with {"objects": [...]}
        - dict with {"annotations": [...]}
        - list of frames: [{"frameName":...,"objects":[...]}]
        - custom CCTV JSON with contour->points
        """
        boxes = []

        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            logging.error(f"Failed to parse JSON: {e}")
            return boxes

        # ------------------------------------------------------------
        # CASE 1 → List of frames
        # ------------------------------------------------------------
        if isinstance(data, list):
            # Find the matching item for this image
            img_name = os.path.basename(self.image_files[self.current_index])
            target_base = os.path.splitext(img_name)[0]

            matched = None
            for item in data:
                if not isinstance(item, dict):
                    continue
                # match frameName without ext
                fn = item.get("frameName") or item.get("image")
                if not fn:
                    continue
                if os.path.splitext(fn)[0] == target_base:
                    matched = item
                    break

            if matched:
                boxes = self._extract_boxes_from_item(matched)
            else:
                logging.warning(f"No matching frame found in JSON list for {img_name}")
                return []

            # If boxes appear normalized (0..1), convert to pixel coords using current image
            try:
                if boxes and self.canvas and getattr(self.canvas, 'image', None) is not None:
                    img_h, img_w = self.canvas.image.shape[:2]
                    vals = [v for box in boxes for v in box[:4]]
                    if vals and max(vals) <= 1.0:
                        logging.debug("Detected normalized per-image JSON bboxes — converting to pixel coords")
                        conv = []
                        for bx, by, bw, bh, cid in boxes:
                            x_px = (bx - bw / 2) * img_w
                            y_px = (by - bh / 2) * img_h
                            w_px = bw * img_w
                            h_px = bh * img_h
                            conv.append((x_px, y_px, w_px, h_px, cid))
                        boxes = conv
            except Exception:
                pass

            return boxes

        # ------------------------------------------------------------
        # CASE 2 → Single dict
        # ------------------------------------------------------------
        if isinstance(data, dict):
            boxes = self._extract_boxes_from_item(data)
            try:
                if boxes and self.canvas and getattr(self.canvas, 'image', None) is not None:
                    img_h, img_w = self.canvas.image.shape[:2]
                    vals = [v for box in boxes for v in box[:4]]
                    if vals and max(vals) <= 1.0:
                        logging.debug("Detected normalized per-image JSON bboxes — converting to pixel coords")
                        conv = []
                        for bx, by, bw, bh, cid in boxes:
                            x_px = (bx - bw / 2) * img_w
                            y_px = (by - bh / 2) * img_h
                            w_px = bw * img_w
                            h_px = bh * img_h
                            conv.append((x_px, y_px, w_px, h_px, cid))
                        boxes = conv
            except Exception:
                pass

            return boxes

    def _get_json_classname_for_box(self, img_name, box):
        """Try to locate the original object's className for a given box by
        scanning the per-image JSON and matching bbox/contour coordinates.
        Returns a string className or None.
        """
        if not img_name:
            return None

        # Determine JSON file path (main folder or converted_json)
        base = os.path.splitext(img_name)[0]
        candidates = [
            os.path.join(self.label_dir, base + ".json"),
            os.path.join(self.label_dir, "converted_json", base + ".json")
        ]

        data = None
        # Use a small per-image cache to avoid repeated file reads when querying
        # multiple boxes for the same image.
        cache_key = None
        if img_name:
            cache_key = os.path.basename(img_name)
        try:
            if hasattr(self, '_last_json_cache') and self._last_json_cache.get('path_key') == cache_key:
                data = self._last_json_cache.get('data')
        except Exception:
            data = None
        for p in candidates:
            logging.debug(f"_get_json_classname_for_box: checking candidate path: {p}")
            if os.path.exists(p):
                logging.debug(f"_get_json_classname_for_box: found file: {p}")
                try:
                    with open(p, 'r') as f:
                        data = json.load(f)
                    # persist cache
                    try:
                        self._last_json_cache = {'path_key': cache_key, 'data': data, 'path': p}
                    except Exception:
                        pass
                    break
                except Exception as e:
                    logging.debug(f"_get_json_classname_for_box: failed to read {p}: {e}")
                    continue

        if data is None:
            return None

        # If list, find matching frame
        if isinstance(data, list):
            target_base = base
            matched = None
            for item in data:
                if not isinstance(item, dict):
                    continue
                fn = item.get('frameName') or item.get('image')
                if not fn:
                    continue
                if os.path.splitext(fn)[0] == target_base:
                    matched = item
                    break
            if matched:
                data = matched
            else:
                return None

        if not isinstance(data, dict):
            return None

        objects = data.get('objects') or data.get('annotations') or []

        # Target bbox
        tx, ty, tw, th, _ = box

        # Tolerance: a small fraction of box size or fixed pixels
        tol = max(3, int(min(tw, th) * 0.05))

        for obj in objects:
            logging.debug(f"_get_json_classname_for_box: checking object with keys: {list(obj.keys())}")
            # compute bbox for object similar to _extract_boxes_from_item
            if 'contour' in obj and 'points' in obj.get('contour', {}):
                pts = obj['contour']['points']
                if len(pts) >= 2:
                    try:
                        x1, y1 = pts[0].get('x'), pts[0].get('y')
                        x2, y2 = pts[1].get('x'), pts[1].get('y')
                    except Exception:
                        continue
                    if None in (x1, y1, x2, y2):
                        continue
                    ox = min(x1, x2)
                    oy = min(y1, y2)
                    ow = abs(x2 - x1)
                    oh = abs(y2 - y1)
                else:
                    continue
            elif 'bbox' in obj and len(obj['bbox']) == 4:
                ox, oy, ow, oh = obj['bbox']
            else:
                continue

            # Compare centers and size similarity
            if abs((ox + ow/2) - (tx + tw/2)) <= tol and abs((oy + oh/2) - (ty + th/2)) <= tol:
                # matched — return className if present
                # Prefer textual extraction using the generic helper (covers many keys)
                try_name = self._get_name_from_object(obj)
                if isinstance(try_name, str) and try_name.strip():
                    logging.debug(f"_get_json_classname_for_box: matched candidate object bbox center; found name={try_name!r}")
                    return try_name.strip()
                # check category container as fallback
                cat = obj.get('category')
                if isinstance(cat, dict):
                    nm = cat.get('name') or cat.get('label')
                    if isinstance(nm, str) and nm.strip():
                        logging.debug(f"_get_json_classname_for_box: matched candidate category.name={nm!r}")
                        return nm.strip()
                if isinstance(cat, str) and cat.strip():
                    logging.debug(f"_get_json_classname_for_box: matched candidate category string={cat!r}")
                    return cat.strip()
                # maybe category_id maps to known class name
                cid = obj.get('classId') or obj.get('category_id')
                try:
                    cid = int(cid)
                    classes = self.class_manager.get_classes()
                    if 0 <= cid < len(classes):
                        return classes[cid]
                except Exception:
                    pass

        return None

        return boxes


    def _extract_boxes_from_item(self, item):
        """
        Extract bounding boxes from ANY per-image JSON item.
        Supports:
            - CCTV contour/points
            - bbox
            - className / classId / category_id
        """

        boxes = []

        # Get objects/annotations
        objects = item.get("objects") or item.get("annotations") or []

        # class map from loaded classes.txt
        classes_list = self.class_manager.get_classes()
        class_map = {name: idx for idx, name in enumerate(classes_list)}
        # build a normalized name -> idx map for fuzzy matching (case/format differences)
        normalized_map = {}
        try:
            for idx, name in enumerate(classes_list):
                norm = self._normalize_label(name) or name
                normalized_map[norm] = idx
        except Exception:
            normalized_map = {}

        for obj in objects:

            # -----------------------------------------------------------
            # 1) UNIVERSAL BBOX EXTRACTION
            # -----------------------------------------------------------

            # CCTV contour → points list
            if "contour" in obj and "points" in obj.get("contour", {}):
                pts = obj["contour"]["points"]
                if len(pts) >= 2:
                    x1, y1 = pts[0].get("x"), pts[0].get("y")
                    x2, y2 = pts[1].get("x"), pts[1].get("y")

                    # Validate
                    if None in (x1, y1, x2, y2):
                        continue

                    x = min(x1, x2)
                    y = min(y1, y2)
                    w = abs(x2 - x1)
                    h = abs(y2 - y1)
                else:
                    continue

            # Normal bbox format
            elif "bbox" in obj and len(obj["bbox"]) == 4:
                x, y, w, h = obj["bbox"]

            else:
                continue  # No bbox → skip object

            # -----------------------------------------------------------
            # 2) UNIVERSAL CLASS RESOLUTION
            # -----------------------------------------------------------

            cls_id = 0  # fallback default

            # Debug: show incoming class fields for this object
            logging.debug(f"JSON object fields: className={obj.get('className')!r}, classId={obj.get('classId')!r}, category_id={obj.get('category_id')!r}, category_name={obj.get('category_name')!r}")

            # Preferred: textual name → id lookup (support many key variants)
            try_name = self._get_name_from_object(obj)
            if isinstance(try_name, str):
                tstrip = try_name.strip()
                # exact match first
                if tstrip in class_map:
                    cls_id = class_map[tstrip]
                    logging.debug(f"Resolved by textual name '{try_name}' -> id {cls_id} (exact)")
                else:
                    # try normalized lookup (case/punctuation-insensitive)
                    norm = self._normalize_label(tstrip)
                    if norm and norm in normalized_map:
                        cls_id = normalized_map[norm]
                        logging.debug(f"Resolved by normalized name '{try_name}' -> id {cls_id} (normalized)")

            # If numeric ID exists, use it (but later validate against known classes)
            elif isinstance(obj.get("classId"), int):
                cls_id = obj["classId"]
                logging.debug(f"Using numeric classId -> {cls_id}")

            # category_id may be int or string; handle both
            elif obj.get("category_id") is not None or obj.get('category') is not None:
                cid = obj.get("category_id")
                # if it's a string name, map it
                # If category is provided as a separate 'category' container, use it when available
                if cid is None:
                    cid = obj.get('category')

                if isinstance(cid, str):
                    if cid in class_map:
                        cls_id = class_map[cid]
                        logging.debug(f"Mapped category_id string '{cid}' -> id {cls_id}")
                    else:
                        # try with stripped name
                        cid_strip = cid.strip()
                        cls_id = class_map.get(cid_strip, cls_id)
                        logging.debug(f"Tried stripped category_id '{cid_strip}' -> {cls_id}")
                else:
                    try:
                        cls_id = int(cid)
                        logging.debug(f"Parsed numeric category_id -> {cls_id}")
                    except Exception:
                        logging.debug(f"Failed to parse category_id: {cid}")

            # Validate int and remap if out-of-range
            try:
                cls_id = int(cls_id)
            except Exception:
                logging.debug(f"cls_id not int-convertible, falling back to 0 (was: {cls_id})")
                cls_id = 0

            # If numeric id is outside known classes, try to resolve by name keys
            if (cls_id < 0) or (len(classes_list) and cls_id >= len(classes_list)):
                # try category_name or className mapping
                cname_try = obj.get('category_name') or obj.get('className')
                if isinstance(cname_try, str) and cname_try.strip() in class_map:
                    cls_id = class_map[cname_try.strip()]
                    logging.debug(f"Remapped out-of-range id by name '{cname_try}' -> {cls_id}")
                else:
                    # fallback to 0 to avoid huge indices
                    logging.debug(f"Class id {cls_id} out of range and no matching name found. Falling back to 0.")
                    cls_id = 0

            # -----------------------------------------------------------
            # Append final bbox
            # -----------------------------------------------------------
            logging.debug(f"Appending box: x={x},y={y},w={w},h={h}, resolved_class_id={cls_id}")
            boxes.append((x, y, w, h, cls_id))

        return boxes



    def _load_coco_boxes(self, file_path, image_name):
        """Load boxes from COCO-style annotations."""
        try:
            with open(file_path, "r") as f:
                coco = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load COCO file '{file_path}': {e}")
            return []
        
        boxes = []
        img_id = None
        
        # Debug: log available images
        available_images = [img["file_name"] for img in coco.get("images", [])]
        logging.debug(f"COCO file has {len(available_images)} images. Looking for: '{image_name}'")
        
        # Try exact match first
        for img in coco.get("images", []):
            if img["file_name"] == image_name:
                img_id = img["id"]
                logging.debug(f"Found exact match for '{image_name}' with image_id={img_id}")
                break
        
        # If no exact match and image not found, log warning
        if img_id is None:
            logging.warning(
                f"Image '{image_name}' not found in COCO file. "
                f"Available images: {available_images[:5]}{'...' if len(available_images) > 5 else ''}"
            )
            return []
        
        # Load annotations for this image
        # Map COCO category_id -> local class index when possible
        coco_id_to_index = getattr(self, 'json_coco_id_to_index', None)
        coco_map = getattr(self, 'json_coco_category_map', None)
        classes_list = self.class_manager.get_classes()

        # ONLY build mapping if not already cached (to preserve class consistency across frames)
        if coco_id_to_index is None or coco_map is None:
            try:
                cats = coco.get('categories', [])
                if isinstance(cats, list) and cats:
                    # Build ordered list of category names and id->index map from the COCO file
                    # Use the order provided in the file (preserves intended mapping)
                    file_cat_names = []
                    file_cid_to_idx = {}
                    for idx, cat in enumerate(cats):
                        if isinstance(cat, dict):
                            cid = None
                            try:
                                cid = int(cat.get('id')) if cat.get('id') is not None else None
                            except Exception:
                                cid = None
                            name = cat.get('name') or cat.get('label') or f"cat_{idx}"
                            file_cat_names.append(name)
                            if cid is not None:
                                file_cid_to_idx[cid] = idx

                    # If current classes don't match COCO categories (or are empty), prefer COCO categories
                    # This keeps canvas/class lists consistent with the COCO annotation file.
                    normalized_current = [self._normalize_label(x) for x in classes_list] if classes_list else []
                    normalized_file = [self._normalize_label(x) for x in file_cat_names]
                    if not normalized_current or normalized_current != normalized_file:
                        try:
                            self.class_manager.classes = file_cat_names
                            self.canvas.classes = file_cat_names
                            logging.info(f"Aligned in-memory classes to COCO categories from '{file_path}' ({len(file_cat_names)} classes)")
                        except Exception:
                            pass

                    # Store maps for future frame loads (cache them to preserve consistency)
                    setattr(self, 'json_coco_category_map', {cid: name for cid, name in ((cid, file_cat_names[idx]) for cid, idx in file_cid_to_idx.items())})
                    setattr(self, 'json_coco_id_to_index', file_cid_to_idx)
                    coco_id_to_index = getattr(self, 'json_coco_id_to_index', None)
                    coco_map = getattr(self, 'json_coco_category_map', None)
                    classes_list = self.class_manager.get_classes()
            except Exception:
                pass

        for ann in coco.get("annotations", []):
            if ann["image_id"] == img_id:
                x, y, w, h = ann["bbox"]
                cat_id = ann.get("category_id")
                # Normalize category id to int when possible (COCO ids may be strings)
                cid = None
                try:
                    if cat_id is not None:
                        cid = int(cat_id)
                except Exception:
                    cid = None
                cls_idx = None

                # Prefer mapping from persisted COCO id -> index
                try:
                    if coco_id_to_index and cid is not None and cid in coco_id_to_index:
                        cls_idx = coco_id_to_index[cid]
                    elif coco_map and cid is not None and cid in coco_map:
                        # find class index by name
                        name = coco_map.get(cid)
                        if name in classes_list:
                            cls_idx = classes_list.index(name)
                        else:
                            # try normalized match
                            norm = self._normalize_label(name)
                            for i, c in enumerate(classes_list):
                                if self._normalize_label(c) == norm:
                                    cls_idx = i
                                    break
                    else:
                        # as a last resort, if category ids are 1-based contiguous and
                        # classes were loaded in the same order, try zero-based shift
                        if cid is not None and 1 <= cid <= len(classes_list):
                            cls_idx = cid - 1
                except Exception:
                    cls_idx = None

                # Fallback to raw category id if no mapping found (will be displayed as Class N)
                final_cls = cls_idx if isinstance(cls_idx, int) else (cid if cid is not None else 0)
                boxes.append((x, y, w, h, final_cls))
        
        logging.debug(f"Loaded {len(boxes)} annotations for '{image_name}'")
        # Heuristic: if bboxes look normalized (values in 0..1), convert to pixels
        try:
            if boxes and self.canvas and getattr(self.canvas, 'image', None) is not None:
                img_h, img_w = self.canvas.image.shape[:2]
                # check if all bbox coords are within [0,1]
                vals = [v for box in boxes for v in box[:4]]
                if vals and max(vals) <= 1.0:
                    logging.debug("Detected normalized COCO-style bboxes in JSON — converting to pixel coords using current image size")
                    conv = []
                    for bx, by, bw, bh, cid in boxes:
                        # some JSONs store bbox as center-based (xc,yc,w,h) — try center->tl conversion
                        # compute top-left from center
                        x_px = (bx - bw / 2) * img_w
                        y_px = (by - bh / 2) * img_h
                        w_px = bw * img_w
                        h_px = bh * img_h
                        conv.append((x_px, y_px, w_px, h_px, cid))
                    boxes = conv
        except Exception:
            pass

        return boxes

    # ----------------------------------------------------------------
    def next_image(self):
        if not self.image_files:
            return
        if self.canvas.changed:
            self.prompt_save_changes()
        
        # Save current selections for this image
        self.image_selections[self.current_index] = self.selected_box_indices.copy()
        
        self.current_index = (self.current_index + 1) % len(self.image_files)
        
        # Clear selections when moving to next image - load_image will set them fresh
        self.selected_box_indices = set()
        
        self.load_image()

    def prev_image(self):
        if not self.image_files:
            return
        if self.canvas.changed:
            self.prompt_save_changes()
        
        # Save current selections for this image
        self.image_selections[self.current_index] = self.selected_box_indices.copy()
        
        self.current_index = (self.current_index - 1) % len(self.image_files)
        
        # Clear selections when moving to previous image - load_image will set them fresh
        self.selected_box_indices = set()
        
        self.load_image()

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
        if self.mode == "view" or not self.image_files or not self.format:
            return
        img_name = self.image_files[self.current_index]
        boxes = self.canvas.boxes

        if self.format == "TXT":
            os.makedirs(self.label_dir, exist_ok=True)
            # Save TXT format - convert from pixel coords to normalized
            label_file = os.path.join(self.label_dir, os.path.splitext(img_name)[0] + ".txt")
            img_h, img_w = self.canvas.image.shape[:2]
            
            with open(label_file, "w") as f:
                for box in boxes:
                    x, y, w, h, class_id = box
                    # Convert to normalized TXT format
                    xc = (x + w / 2) / img_w
                    yc = (y + h / 2) / img_h
                    bw = w / img_w
                    bh = h / img_h
                    f.write(f"{int(class_id)} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")
        elif self.format == "JSON":
            os.makedirs(self.label_dir, exist_ok=True)
            save_json(self.label_dir, img_name, boxes, "")
        elif self.format == "COCO":
            # Save COCO format to the specific COCO file path
            if self.coco_file_path:
                self._save_coco_annotation(img_name, boxes)
            else:
                QMessageBox.warning(self, "Error", "COCO file path not set. Cannot save.")
                logging.error("COCO file path not set. Cannot save annotation.")
                return

        self.canvas.changed = False
        self.app_status_bar.set_status(get_status_message("image_saved"))
        logging.info(f"Saved annotations for '{img_name}' ({len(boxes)} boxes) format={self.format}")
        if not auto:
            QMessageBox.information(self, "Saved", f"Saved {img_name}")

    def _save_coco_annotation(self, img_name, boxes):
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
            
            # Build category map
            classes = self.class_manager.get_classes()
            name_to_cid = {}
            for cat in coco.get("categories", []):
                if isinstance(cat, dict):
                    nm = cat.get("name") or cat.get("label")
                    cid = cat.get("id")
                    if nm is not None and cid is not None:
                        name_to_cid[str(nm).strip()] = cid
            
            # Add new annotations
            max_ann_id = max([ann.get("id", 0) for ann in coco.get("annotations", [])], default=0)
            
            for i, box in enumerate(boxes, start=1):
                x, y, w, h, class_id = box
                
                # Map class_id to category_id
                cid_to_write = None
                try:
                    if isinstance(class_id, int) and 0 <= class_id < len(classes):
                        cname = classes[class_id]
                        if cname in name_to_cid:
                            cid_to_write = name_to_cid[cname]
                        else:
                            # Try normalized matching
                            norm = ''.join(ch for ch in cname.lower() if ch.isalnum() or ch.isspace()).strip()
                            for nm, cid in name_to_cid.items():
                                nm_norm = ''.join(ch for ch in nm.lower() if ch.isalnum() or ch.isspace()).strip()
                                if nm_norm == norm:
                                    cid_to_write = cid
                                    break
                except Exception:
                    cid_to_write = None
                
                if cid_to_write is None:
                    try:
                        cid_to_write = int(class_id)
                    except Exception:
                        cid_to_write = 0
                
                coco["annotations"].append({
                    "id": max_ann_id + i,
                    "image_id": image_id,
                    "category_id": int(cid_to_write),
                    "bbox": [x, y, w, h],
                    "area": w * h,
                    "iscrowd": 0
                })
            
            # Write back to file
            with open(self.coco_file_path, 'w') as f:
                json.dump(coco, f, indent=2)
            
            logging.info(f"Saved {len(boxes)} annotations to {self.coco_file_path}")
        
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
            converted_files = convert_txt_to_json(self.label_dir, output_dir=None, img_size=None)
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
            from PyQt5.QtWidgets import QFormLayout, QLineEdit, QDialogButtonBox

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