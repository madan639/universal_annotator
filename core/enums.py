from enum import Enum

class AppMode(Enum):
    DETECTION = "detection"
    SEGMENTATION = "segmentation"

class DrawingTool(Enum):
    RECTANGLE = "rectangle"
    POLYGON = "polygon"
