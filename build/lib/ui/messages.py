"""Tooltips and Status Messages Configuration"""

TOOLTIPS = {
    # File Operations
    "load_dataset": "Click to load image and label folders",
    "format_btn": "Select the annotation format (TXT, JSON, or COCO)",
    
    # Mode Selection
    "edit_mode": "Switch to Edit Mode to create and modify annotations",
    "view_mode": "Switch to View Mode to review annotations (read-only)",
    
    # Navigation
    "prev_btn": "Go to previous image (Press A)",
    "next_btn": "Go to next image (Press D)",
    
    # Annotation Management
    "save_btn": "Save current image annotations (Press S)",
    "select_all_btn": "Select all bounding boxes in current image",
    "deselect_all_btn": "Deselect all bounding boxes in current image",
    
    # Misc
    "auto_save_cb": "Automatically save changes when navigating between images",
}

STATUS_MESSAGES = {
    "edit_mode_enabled": "Edit Mode Enabled - You can now draw and modify bounding boxes",
    "view_mode_enabled": "View Mode Enabled - Read-only mode",
    "dataset_loaded": "Dataset loaded successfully",
    "format_selected": "Annotation format selected",
    "image_saved": "Image annotations saved",
    "no_images": "No images found in the selected folder",
    "no_format": "Please select an annotation format",
    "box_deleted": "Last bounding box deleted",
    "all_selected": "All boxes selected",
    "all_deselected": "All boxes deselected",
}


def get_tooltip(key):
    """Get tooltip for a UI element"""
    return TOOLTIPS.get(key, "")


def get_status_message(key):
    """Get status message"""
    return STATUS_MESSAGES.get(key, "")
