import os
import json
import logging
from PyQt5.QtWidgets import QMessageBox

def save_coco(coco_file_path, img_name, boxes, polygons=None):
    """
    Update a COCO JSON file with annotations for a specific image.
    
    Args:
        coco_file_path: Path to the COCO JSON file
        img_name: File name of the image
        boxes: List of bounding boxes [(x, y, w, h, class_id), ...]
        polygons: Optional list of polygons [([(x,y), ...], class_id), ...]
    """
    try:
        # Read existing COCO file
        if os.path.exists(coco_file_path):
            with open(coco_file_path, 'r') as f:
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
            logging.warning(f"Image '{img_name}' not found in COCO file. Cannot save annotations.")
            return False
        
        # Remove existing annotations for this image
        coco["annotations"] = [ann for ann in coco.get("annotations", []) if ann.get("image_id") != image_id]
        
        # Generate new IDs
        # We try to use a unique starting ID to avoid collisions if possible, 
        # or just use the next available ID.
        start_id = 900000 + image_id * 1000
        if coco["annotations"]:
             max_id = max(ann.get("id", 0) for ann in coco["annotations"])
             start_id = max_id + 1
        else:
             start_id = 1

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
                  
                  # Calculate bbox from polygon
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
        
        with open(coco_file_path, 'w') as f:
            json.dump(coco, f, indent=2)
            
        logging.info(f"Updated COCO file '{coco_file_path}' for image '{img_name}'")
        return True
    
    except Exception as e:
        logging.error(f"Error saving COCO annotation: {e}")
        QMessageBox.warning("Error", f"Failed to save COCO annotation:\n{str(e)}")
        return False
