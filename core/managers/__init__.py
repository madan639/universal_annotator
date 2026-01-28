"""
Manager classes for Universal Annotator.

These managers extract logic from the monolithic app_window.py
for better modularity and maintainability.
"""

from .image_manager import ImageManager
from .annotation_manager import AnnotationManager
from .format_manager import FormatManager
from .autosave_manager import AutoSaveManager

__all__ = [
    'ImageManager',
    'AnnotationManager',
    'FormatManager',
    'AutoSaveManager',
]
