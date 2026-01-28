"""
AnnotationManager - Handles annotation operations (add, delete, update, selection).

This manager is responsible for:
- Managing bounding boxes for the current image
- Adding, deleting, and updating annotations
- Managing multi-selection state
- Future support for polygons, keypoints, and masks
"""

import logging
from typing import List, Tuple, Set, Optional, Dict


class AnnotationManager:
    """Manages annotations (bounding boxes) for images."""
    
    # Annotation format: (x, y, w, h, class_id)
    # where x, y is top-left corner, w, h are dimensions
    
    def __init__(self):
        """Initialize the AnnotationManager."""
        self.boxes: List[Tuple[float, float, float, float, int]] = []
        self.selected_indices: Set[int] = set()
        self.changed: bool = False
        # For tracking selections across images
        self.image_selections: Dict[int, Set[int]] = {}
        self.manual_deselect_all: bool = False
    
    def add_box(self, box: Tuple[float, float, float, float, int]) -> int:
        """
        Add a new bounding box.
        
        Args:
            box: Tuple of (x, y, w, h, class_id)
            
        Returns:
            int: Index of the newly added box
        """
        self.boxes.append(box)
        new_index = len(self.boxes) - 1
        self.selected_indices.add(new_index)
        self.changed = True
        logging.debug(f"Added box at index {new_index}: {box}")
        return new_index
    
    def delete_box(self, index: int) -> bool:
        """
        Delete a bounding box by index.
        
        Args:
            index: Index of box to delete
            
        Returns:
            bool: True if deleted successfully, False if index invalid
        """
        if 0 <= index < len(self.boxes):
            deleted_box = self.boxes.pop(index)
            
            # Update selected indices
            if index in self.selected_indices:
                self.selected_indices.remove(index)
            
            # Reindex selections after deletion
            new_selected = set()
            for idx in self.selected_indices:
                if idx > index:
                    new_selected.add(idx - 1)
                else:
                    new_selected.add(idx)
            self.selected_indices = new_selected
            
            self.changed = True
            logging.debug(f"Deleted box at index {index}: {deleted_box}")
            return True
        else:
            logging.warning(f"Cannot delete box: invalid index {index}")
            return False
    
    def delete_boxes(self, indices: List[int]) -> int:
        """
        Delete multiple bounding boxes.
        
        Args:
            indices: List of indices to delete
            
        Returns:
            int: Number of boxes actually deleted
        """
        if not indices:
            return 0
        
        # Sort in reverse to delete from end to start (avoids index shifting issues)
        sorted_indices = sorted(set(indices), reverse=True)
        deleted_count = 0
        
        for idx in sorted_indices:
            if self.delete_box(idx):
                deleted_count += 1
        
        logging.info(f"Deleted {deleted_count} boxes")
        return deleted_count
    
    def update_box(self, index: int, box: Tuple[float, float, float, float, int]) -> bool:
        """
        Update an existing bounding box.
        
        Args:
            index: Index of box to update
            box: New box data (x, y, w, h, class_id)
            
        Returns:
            bool: True if updated successfully, False if index invalid
        """
        if 0 <= index < len(self.boxes):
            old_box = self.boxes[index]
            self.boxes[index] = box
            self.changed = True
            logging.debug(f"Updated box {index}: {old_box} -> {box}")
            return True
        else:
            logging.warning(f"Cannot update box: invalid index {index}")
            return False
    
    def get_boxes(self) -> List[Tuple[float, float, float, float, int]]:
        """
        Get all bounding boxes.
        
        Returns:
            List of boxes as (x, y, w, h, class_id) tuples
        """
        return self.boxes.copy()
    
    def set_boxes(self, boxes: List[Tuple[float, float, float, float, int]]) -> None:
        """
        Set all bounding boxes (replaces existing).
        
        Args:
            boxes: List of boxes to set
        """
        self.boxes = boxes.copy()
        self.changed = True
        logging.debug(f"Set {len(boxes)} boxes")
    
    def select_box(self, index: int) -> bool:
        """
        Add a box to the selection.
        
        Args:
            index: Index of box to select
            
        Returns:
            bool: True if selected successfully, False if index invalid
        """
        if 0 <= index < len(self.boxes):
            self.selected_indices.add(index)
            logging.debug(f"Selected box {index}")
            return True
        else:
            logging.warning(f"Cannot select box: invalid index {index}")
            return False
    
    def deselect_box(self, index: int) -> bool:
        """
        Remove a box from the selection.
        
        Args:
            index: Index of box to deselect
            
        Returns:
            bool: True if deselected, False if wasn't selected or invalid index
        """
        if index in self.selected_indices:
            self.selected_indices.remove(index)
            logging.debug(f"Deselected box {index}")
            return True
        return False
    
    def select_all(self) -> None:
        """Select all boxes."""
        self.selected_indices = set(range(len(self.boxes)))
        self.manual_deselect_all = False
        logging.debug(f"Selected all {len(self.boxes)} boxes")
    
    def deselect_all(self) -> None:
        """Deselect all boxes."""
        self.selected_indices.clear()
        self.manual_deselect_all = True
        logging.debug("Deselected all boxes")
    
    def get_selected_indices(self) -> Set[int]:
        """
        Get indices of currently selected boxes.
        
        Returns:
            Set of selected indices
        """
        return self.selected_indices.copy()
    
    def get_box_count(self) -> int:
        """
        Get total number of boxes.
        
        Returns:
            int: Number of boxes
        """
        return len(self.boxes)
    
    def is_changed(self) -> bool:
        """
        Check if annotations have been modified.
        
        Returns:
            bool: True if modified since last save
        """
        return self.changed
    
    def mark_saved(self) -> None:
        """Mark annotations as saved (clear changed flag)."""
        self.changed = False
        logging.debug("Annotations marked as saved")
    
    def clear(self) -> None:
        """Clear all annotations and selections."""
        self.boxes = []
        self.selected_indices.clear()
        self.changed = False
        logging.debug("Cleared all annotations")
    
    def save_selection_state(self, image_index: int) -> None:
        """
        Save current selection state for an image.
        
        Args:
            image_index: Index of the image
        """
        self.image_selections[image_index] = self.selected_indices.copy()
    
    def restore_selection_state(self, image_index: int) -> bool:
        """
        Restore selection state for an image.
        
        Args:
            image_index: Index of the image
            
        Returns:
            bool: True if state was restored, False if no saved state
        """
        if image_index in self.image_selections:
            saved = self.image_selections[image_index]
            # Only restore valid indices
            self.selected_indices = {idx for idx in saved if idx < len(self.boxes)}
            logging.debug(f"Restored selection state for image {image_index}: {len(self.selected_indices)} boxes")
            return True
        return False
