"""
FormatManager - Handles loading and saving annotations in different formats.

This manager is responsible for:
- Loading annotations from TXT, JSON, and COCO formats
- Saving annotations to different formats
- Format detection and conversion
- Interfacing with converter scripts
"""

import os
import json
import logging
from typing import List, Tuple, Optional, Dict, Any


class FormatManager:
    """Manages annotation format loading, saving, and conversion."""
    
    SUPPORTED_FORMATS = ["TXT", "JSON", "COCO"]
    
    def __init__(self):
        """Initialize the FormatManager."""
        self.current_format: str = "TXT"  # Default format
        self.label_dir: str = ""
    
    def set_label_directory(self, label_dir: str) -> None:
        """
        Set the label directory path.
        
        Args:
            label_dir: Path to the label directory
        """
        self.label_dir = label_dir
        logging.debug(f"Label directory set to: {label_dir}")
    
    def set_format(self, format_name: str) -> bool:
        """
        Set the current annotation format.
        
        Args:
            format_name: One of "TXT", "JSON", "COCO"
            
        Returns:
            bool: True if format is valid and set, False otherwise
        """
        if format_name in self.SUPPORTED_FORMATS:
            self.current_format = format_name
            logging.info(f"Annotation format set to: {format_name}")
            return True
        else:
            logging.warning(f"Unsupported format: {format_name}")
            return False
    
    def get_format(self) -> str:
        """
        Get the current annotation format.
        
        Returns:
            str: Current format name
        """
        return self.current_format
    
    def detect_format(self) -> Optional[str]:
        """
        Auto-detect annotation format from files in label directory.
        
        Returns:
            str: Detected format ("TXT", "JSON", "COCO") or None if detection fails
        """
        if not self.label_dir or not os.path.isdir(self.label_dir):
            logging.warning("Label directory not set or doesn't exist")
            return None
        
        try:
            files = os.listdir(self.label_dir)
            
            # Check for COCO format
            if "_annotations.coco.json" in files:
                logging.info("Detected COCO format")
                return "COCO"
            
            # Check for JSON files
            json_files = [f for f in files if f.endswith('.json')]
            if json_files:
                logging.info("Detected JSON format")
                return "JSON"
            
            # Check for TXT files
            txt_files = [f for f in files if f.endswith('.txt') and f != 'classes.txt']
            if txt_files:
                logging.info("Detected TXT format")
                return "TXT"
            
            logging.warning("Could not detect format from label directory")
            return None
            
        except Exception as e:
            logging.error(f"Error detecting format: {e}")
            return None
    
    def load_txt_boxes(self, file_path: str, img_shape: Tuple[int, int]) -> List[Tuple[float, float, float, float, int]]:
        """
        Load bounding boxes from TXT file (YOLO format).
        
        Args:
            file_path: Path to the TXT file
            img_shape: Image dimensions as (height, width)
            
        Returns:
            List of boxes as (x, y, w, h, class_id) tuples in pixel coordinates
        """
        boxes = []
        if not os.path.exists(file_path):
            return boxes
        
        img_h, img_w = img_shape
        
        try:
            with open(file_path, "r") as f:
                for line in f:
                    vals = line.strip().split()
                    if len(vals) < 5:
                        continue
                    
                    cls = int(vals[0])
                    xc, yc, bw, bh = map(float, vals[1:5])
                    
                    # Convert from normalized to pixel coordinates
                    x = (xc - bw / 2) * img_w
                    y = (yc - bh / 2) * img_h
                    w = bw * img_w
                    h = bh * img_h
                    
                    boxes.append((x, y, w, h, cls))
                    
            logging.debug(f"Loaded {len(boxes)} boxes from TXT file: {file_path}")
            
        except Exception as e:
            logging.error(f"Error loading TXT file {file_path}: {e}")
        
        return boxes
    
    def save_txt_box(self, file_path: str, box: Tuple[float, float, float, float, int], 
                     img_shape: Tuple[int, int], mode: str = 'a') -> bool:
        """
        Save a single bounding box to TXT file (YOLO format).
        
        Args:
            file_path: Path to the TXT file
            box: Box as (x, y, w, h, class_id) in pixel coordinates
            img_shape: Image dimensions as (height, width)
            mode: File open mode ('a' for append, 'w' for write)
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            img_h, img_w = img_shape
            x, y, w, h, cls = box
            
            # Convert to normalized YOLO format
            xc = (x + w / 2) / img_w
            yc = (y + h / 2) / img_h
            bw = w / img_w
            bh = h / img_h
            
            with open(file_path, mode) as f:
                f.write(f"{int(cls)} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")
            
            return True
            
        except Exception as e:
            logging.error(f"Error saving to TXT file {file_path}: {e}")
            return False
    
    def save_txt_boxes(self, file_path: str, boxes: List[Tuple[float, float, float, float, int]], 
                       img_shape: Tuple[int, int]) -> bool:
        """
        Save all bounding boxes to TXT file (YOLO format).
        
        Args:
            file_path: Path to the TXT file
            boxes: List of boxes as (x, y, w, h, class_id) in pixel coordinates
            img_shape: Image dimensions as (height, width)
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            img_h, img_w = img_shape
            
            with open(file_path, 'w') as f:
                for box in boxes:
                    x, y, w, h, cls = box
                    
                    # Convert to normalized YOLO format
                    xc = (x + w / 2) / img_w
                    yc = (y + h / 2) / img_h
                    bw = w / img_w
                    bh = h / img_h
                    
                    f.write(f"{int(cls)} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")
            
            logging.debug(f"Saved {len(boxes)} boxes to TXT file: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving TXT file {file_path}: {e}")
            return False
    
    def get_annotation_path(self, image_name: str) -> Optional[str]:
        """
        Get the annotation file path for a given image.
        
        Args:
            image_name: Name of the image file
            
        Returns:
            str: Path to annotation file, or None if format not supported
        """
        if not self.label_dir:
            return None
        
        base_name = os.path.splitext(image_name)[0]
        
        if self.current_format == "TXT":
            return os.path.join(self.label_dir, f"{base_name}.txt")
        elif self.current_format == "JSON":
            return os.path.join(self.label_dir, f"{base_name}.json")
        elif self.current_format == "COCO":
            return os.path.join(self.label_dir, "_annotations.coco.json")
        
        return None
