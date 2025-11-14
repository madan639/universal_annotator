"""Menu Bar Creation for Application"""
from PyQt5.QtWidgets import QMenuBar, QApplication
from PyQt5.QtGui import QKeySequence


class AppMenuBar(QMenuBar):
    """Custom menu bar with all application menus"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self._create_menus()
    
    def _create_menus(self):
        """Create all menu items"""
        self._create_file_menu()
        self._create_edit_menu()
        self._create_view_menu()
        self._create_help_menu()
    
    def _create_file_menu(self):
        """Create File menu"""
        file_menu = self.addMenu("File")
        
        # Load Dataset
        load_action = file_menu.addAction("Load Dataset")
        load_action.setShortcut(QKeySequence.Open)
        load_action.setStatusTip("Load images and annotations")
        load_action.triggered.connect(self.parent.load_dataset)
        
        # Select Format
        format_action = file_menu.addAction("Select Format")
        format_action.setStatusTip("Choose annotation format")
        format_action.triggered.connect(self.parent.select_format)
        
        file_menu.addSeparator()
        
        # Save
        save_action = file_menu.addAction("Save")
        save_action.setShortcut(QKeySequence.Save)
        save_action.setStatusTip("Save current annotations")
        save_action.triggered.connect(self.parent.save_annotation)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.parent.close_prompt)
    
    def _create_edit_menu(self):
        """Create Edit menu"""
        edit_menu = self.addMenu("Edit")
        
        # Edit Mode
        edit_mode_action = edit_menu.addAction("Edit Mode")
        edit_mode_action.setShortcut("E")
        edit_mode_action.setStatusTip("Switch to Edit Mode")
        edit_mode_action.triggered.connect(self.parent.set_edit_mode)
        
        # View Mode
        view_mode_action = edit_menu.addAction("View Mode")
        view_mode_action.setShortcut("V")
        view_mode_action.setStatusTip("Switch to View Mode")
        view_mode_action.triggered.connect(self.parent.set_view_mode)
        
        edit_menu.addSeparator()
        
        # Delete Selected Boxes
        delete_action = edit_menu.addAction("Delete Selected Boxes")
        delete_action.setShortcut(QKeySequence.Delete)
        delete_action.setStatusTip("Remove the selected bounding boxes")
        delete_action.triggered.connect(self.parent.delete_selected_boxes)
        
        edit_menu.addSeparator()
        
        # Select All
        select_all_action = edit_menu.addAction("Select All Boxes")
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_all_action.setStatusTip("Select all bounding boxes")
        select_all_action.triggered.connect(self.parent.select_all_labels)
        
        # Deselect All
        deselect_action = edit_menu.addAction("Deselect All Boxes")
        deselect_action.setShortcut("Ctrl+D")
        deselect_action.setStatusTip("Deselect all bounding boxes")
        deselect_action.triggered.connect(self.parent.deselect_all_labels)
    
    def _create_view_menu(self):
        """Create View menu"""
        view_menu = self.addMenu("View")
        
        # Previous Image
        prev_action = view_menu.addAction("Previous Image")
        prev_action.setShortcut("A")
        prev_action.setStatusTip("Go to previous image")
        prev_action.triggered.connect(self.parent.prev_image)
        
        # Next Image
        next_action = view_menu.addAction("Next Image")
        next_action.setShortcut("D")
        next_action.setStatusTip("Go to next image")
        next_action.triggered.connect(self.parent.next_image)
        
        view_menu.addSeparator()
        
        # Refresh
        refresh_action = view_menu.addAction("Refresh Current Image")
        refresh_action.setShortcut("F5")
        refresh_action.setStatusTip("Reload current image")
        refresh_action.triggered.connect(self.parent.refresh_image)
        
        view_menu.addSeparator()
        
        # Toggle Auto-Save
        auto_save_action = view_menu.addAction("Toggle Auto-Save")
        auto_save_action.setStatusTip("Enable/disable auto-save")
        auto_save_action.triggered.connect(self.parent.toggle_auto_save)
    
    def _create_help_menu(self):
        """Create Help menu"""
        help_menu = self.addMenu("Help")
        
        # Help
        help_action = help_menu.addAction("Help & Shortcuts")
        help_action.setShortcut("F1")
        help_action.setStatusTip("Open help dialog")
        help_action.triggered.connect(self.parent.show_help)
        
        help_menu.addSeparator()
        
        # About
        about_action = help_menu.addAction("About")
        about_action.setStatusTip("About Universal Annotator")
        about_action.triggered.connect(self.parent.show_about)
