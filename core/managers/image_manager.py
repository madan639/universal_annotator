"""
ImageManager - Handles image loading, navigation, and caching.

This manager is responsible for:
- Loading image datasets
- Managing image file list and current index
- Navigation (next/prev/jump)
- Image validation and filtering
"""

import os
import logging
from typing import List, Optional, Tuple


class ImageManager:
    """Manages image file list, current index, and navigation."""
    
    def __init__(self):
        """Initialize the ImageManager."""
        self.image_dir: str = ""
        self.image_files: List[str] = []
        self.current_index: int = 0
        self.supported_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')
    
    def load_dataset(self, image_dir: str) -> bool:
        """
        Load images from the specified directory.
        
        Args:
            image_dir: Path to the directory containing images
            
        Returns:
            bool: True if images were loaded successfully, False otherwise
        """
        if not os.path.isdir(image_dir):
            logging.error(f"Image directory does not exist: {image_dir}")
            return False
        
        self.image_dir = image_dir
        self.image_files = self._get_image_files(image_dir)
        
        if not self.image_files:
            logging.warning(f"No supported images found in {image_dir}")
            return False
        
        self.current_index = 0
        logging.info(f"Loaded {len(self.image_files)} images from {image_dir}")
        return True
   
    def _get_image_files(self, directory: str) -> List[str]:
        """
        Get list of image files from directory.
        
        Args:
            directory: Path to search for images
            
        Returns:
            List of image filenames (not full paths)
        """
        all_files = []
        try:
            all_files = sorted([
                f for f in os.listdir(directory)
                if os.path.isfile(os.path.join(directory, f))
                and f.lower().endswith(self.supported_extensions)
            ])
        except Exception as e:
            logging.error(f"Error reading directory {directory}: {e}")
        
        return all_files
    
    def get_current_image_path(self) -> Optional[str]:
        """
        Get the full path to the current image.
        
        Returns:
            Full path to current image, or None if no images loaded
        """
        if not self.image_files or self.current_index >= len(self.image_files):
            return None
        
        return os.path.join(self.image_dir, self.image_files[self.current_index])
    
    def get_current_image_name(self) -> Optional[str]:
        """
        Get the filename of the current image.
        
        Returns:
            Filename of current image, or None if no images loaded
        """
        if not self.image_files or self.current_index >= len(self.image_files):
            return None
        
        return self.image_files[self.current_index]
    
    def next_image(self) -> bool:
        """
        Move to the next image.
        
        Returns:
            bool: True if moved successfully, False if at end
        """
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            logging.debug(f"Moved to next image: {self.current_index +1}/{len(self.image_files)}")
            return True
        else:
            logging.debug("Already at last image")
            return False
    
    def prev_image(self) -> bool:
        """
        Move to the previous image.
        
        Returns:
            bool: True if moved successfully, False if at beginning
        """
        if self.current_index > 0:
            self.current_index -= 1
            logging.debug(f"Moved to previous image: {self.current_index + 1}/{len(self.image_files)}")
            return True
        else:
            logging.debug("Already at first image")
            return False
    
    def jump_to_index(self, index: int) -> bool:
        """
        Jump to a specific image index.
        
        Args:
            index: Target index (0-based)
            
        Returns:
            bool: True if jump successful, False if index invalid
        """
        if 0 <= index < len(self.image_files):
            self.current_index = index
            logging.debug(f"Jumped to image {index + 1}/{len(self.image_files)}")
            return True
        else:
            logging.warning(f"Invalid index {index}, valid range: 0-{len(self.image_files) - 1}")
            return False
    
    def get_total_images(self) -> int:
        """
        Get total number of images in the dataset.
        
        Returns:
            int: Total number of images
        """
        return len(self.image_files)
    
    def get_progress_info(self) -> Tuple[int, int]:
        """
        Get current progress through the dataset.
        
        Returns:
            Tuple of (current_position, total_images) where current_position is 1-based
        """
        return (self.current_index + 1, len(self.image_files))
    
    def reset(self) -> None:
        """Reset the image manager to initial state."""
        self.image_dir = ""
        self.image_files = []
        self.current_index = 0
        logging.debug("ImageManager reset")
