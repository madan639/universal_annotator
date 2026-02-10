import os
import json
import logging
from typing import List, Tuple, Dict, Any, Optional

# Try relative import if inside package, else absolute/sys.path
try:
    from core.json_helper import JSONHelper
except ImportError:
    JSONHelper = None

# We expect this to be run where core is importable
if JSONHelper is None:
    # Manual fallback for safety 
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.json_helper import JSONHelper

json_helper = JSONHelper()

def load_txt_annotations(file_path: str, img_shape: Tuple[int, int], mode: str = None) -> Tuple[List, List]:
    """
    Load TXT annotations (YOLO style).
    Returns (boxes, polygons).
    boxes: [(x, y, w, h, class_id)]
    polygons: [([(x,y)...], class_id)]
    
    Args:
        file_path: Path to TXT file
        img_shape: (height, width) tuple
        mode: Optional mode filter - "annotation" for boxes only, "segmentation" for polygons only
    """
    img_h, img_w = img_shape
    boxes = []
    polygons = []
    
    try:
        with open(file_path, "r") as f:
            for line in f:
                vals = line.strip().split()
                if not vals:
                    continue
                
                try:
                    class_id = int(vals[0])
                    coords = [float(v) for v in vals[1:]]
                    
                    if len(coords) == 4 and mode != "segmentation":
                        # BBox: xc, yc, bw, bh - only load if not in segmentation mode
                        xc, yc, bw, bh = coords
                        x = (xc - bw / 2) * img_w
                        y = (yc - bh / 2) * img_h
                        w = bw * img_w
                        h = bh * img_h
                        boxes.append((x, y, w, h, class_id))
                    elif len(coords) > 4 and mode != "annotation":
                        # Polygon: x1, y1, x2, y2 ... - only load if not in annotation mode
                        points = []
                        for i in range(0, len(coords), 2):
                            px = coords[i] * img_w
                            py = coords[i+1] * img_h
                            points.append((px, py))
                        polygons.append((points, class_id))
                except ValueError:
                    continue
    except Exception as e:
        logging.error(f"Error loading TXT {file_path}: {e}")
        
    return boxes, polygons  

def load_json_annotations(file_path: str, img_name: str, class_manager, img_shape=None, mode=None) -> Tuple[List, List]:
    """
    Load JSON annotations.
    Returns (boxes, polygons).
    
    Args:
        file_path: Path to JSON file
        img_name: Name of image file
        class_manager: Class manager instance
        img_shape: Optional (height, width) tuple for denormalization
        mode: Optional mode filter - "annotation" for boxes only, "segmentation" for polygons only, None for both
    """
    boxes = []
    polygons = []
    
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            
        target_items = []
        
        # 1. List of frames
        if isinstance(data, list):
             target_base = os.path.splitext(img_name)[0]
             for item in data:
                 if not isinstance(item, dict): continue
                 fn = item.get("frameName") or item.get("image")
                 if fn and os.path.splitext(fn)[0] == target_base:
                     target_items.append(item)
                     break
        # 2. Single dict
        elif isinstance(data, dict):
            target_items.append(data)
            
        if not target_items:
            return [], []
            
        for item in target_items:
            objects = []
            if "objects" in item and isinstance(item["objects"], list):
                objects.extend(item["objects"])
            elif "annotations" in item and isinstance(item["annotations"], list):
                objects.extend(item["annotations"])
            else:
                pass

            for obj in objects:
                # Class resolution: prioritize className for display, fall back to classId
                class_id = 0
                name = json_helper.get_name_from_object(obj)
                
                # If we have a proper class name, use it to register/find the class
                if name and isinstance(name, str) and len(name) < 50:
                    classes = class_manager.get_classes()
                    if name in classes:
                        class_id = classes.index(name)
                    else:
                        # Add this class name to class_manager
                        class_manager.add_class(name)
                        classes = class_manager.get_classes()
                        class_id = classes.index(name)
                elif "classId" in obj:
                    # Only use classId if no className available
                    raw_id = int(obj["classId"])
                    classes = class_manager.get_classes()
                    if raw_id < len(classes):
                        class_id = raw_id
                    else:
                        # Create a placeholder class name
                        placeholder = f"Class_{raw_id}"
                        if placeholder not in classes:
                            class_manager.add_class(placeholder)
                            classes = class_manager.get_classes()
                        class_id = classes.index(placeholder)
                elif "category_id" in obj:
                    raw_id = int(obj["category_id"])
                    classes = class_manager.get_classes()
                    if raw_id < len(classes):
                        class_id = raw_id
                    else:
                        placeholder = f"Class_{raw_id}"
                        if placeholder not in classes:
                            class_manager.add_class(placeholder)
                            classes = class_manager.get_classes()
                        class_id = classes.index(placeholder)

                # Polygon - only load if mode allows
                if mode != "annotation":  # Load polygons unless mode is "annotation"
                    pts = json_helper.extract_polygon_points(obj)
                    if pts:
                        # Check for normalization (all coords <= 1.0)
                        if img_shape and pts:
                            all_vals = []
                            for p in pts:
                                all_vals.extend(p)
                            if all_vals and max(all_vals) <= 1.0:
                                h_img, w_img = img_shape
                                # Scale up
                                pts = [(p[0] * w_img, p[1] * h_img) for p in pts]
                                
                        polygons.append((pts, class_id))
                        continue 
                
                # BBox - only load if mode allows
                if mode != "segmentation":  # Load boxes unless mode is "segmentation"
                    bbox = json_helper.extract_bbox(obj)
                    if bbox:
                        x, y, w, h = bbox
                        if img_shape:
                            # Check normalization heuristic
                             vals = [x, y, w, h]
                             if max(vals) <= 1.0:
                                 h_img, w_img = img_shape
                                 x = x * w_img
                                 y = y * h_img
                                 w = w * w_img
                                 h = h * h_img
                                 # If JSON stored center vals but normalized? Assume TopLeft for now unless logic proves otherwise.
                                 # Existing logic assumed (bx - bw/2) if normalized?
                                 # Let's check existing app_window logic.
                                 # It did: x_px = (bx - bw / 2) * img_w
                                 # So it assumed CENTER coordinates for normalized.
                                 # I should replicate that unless `extract_bbox` already handled it.
                                 # `extract_bbox` returns RAW.
                                 # So I will apply the center->tl conversion for normalized data.
                                 x = (vals[0] - vals[2]/2) * w_img
                                 y = (vals[1] - vals[3]/2) * h_img
                                 w = vals[2] * w_img
                                 h = vals[3] * h_img

                        boxes.append((x, y, w, h, class_id))
                    
    except Exception as e:
        logging.error(f"Error loading JSON {file_path}: {e}")
        
    return boxes, polygons

def load_coco_annotations(file_path: str, img_name: str, class_manager, mode: str = None) -> Tuple[List, List]:
    """Load COCO annotations.
    
    Args:
        file_path: Path to COCO JSON file
        img_name: Name of image file
        class_manager: Class manager instance
        mode: Optional mode filter - "annotation" for boxes only, "segmentation" for polygons only
    """
    boxes = []
    polygons = []
    try:
        with open(file_path, "r") as f:
            coco = json.load(f)
            
        img_id = None
        for img in coco.get("images", []):
            if img["file_name"] == img_name:
                img_id = img["id"]
                break
        
        if img_id is None:
            return [], []
            
        for ann in coco.get("annotations", []):
            if ann["image_id"] == img_id:
                cid = ann.get("category_id", 0)
                
                # Polygon - only load if not in annotation mode
                if mode != "annotation" and "segmentation" in ann and ann["segmentation"]:
                    seg = ann["segmentation"]
                    if isinstance(seg, list) and seg:
                         poly_flat = seg[0]
                         points = [(poly_flat[i], poly_flat[i+1]) for i in range(0, len(poly_flat), 2)]
                         polygons.append((points, cid))
                         continue
                
                # BBox - only load if not in segmentation mode
                if mode != "segmentation" and "bbox" in ann:
                    x, y, w, h = ann["bbox"]
                    boxes.append((x, y, w, h, cid))
                    
    except Exception:
        pass
        
    return boxes, polygons
