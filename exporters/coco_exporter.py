import os, json
import logging

def save_coco(export_dir, img_name, boxes, classes):
    path = os.path.join(export_dir, "_annotations.coco.json")

    # --- Read existing COCO file ---
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                coco = json.load(f)
        except json.JSONDecodeError:
            logging.error(f"Could not decode existing COCO file at {path}. Creating a new one.")
            coco = {"images": [], "annotations": [], "categories": []}
    else:
        # If file doesn't exist, create a new structure
        coco = {
            "info": {"description": "COCO format annotations"},
            "licenses": [],
            "images": [],
            "annotations": [],
            "categories": [{"id": i, "name": name, "supercategory": "none"} for i, name in enumerate(classes)]
        }

    # --- Find image_id for the current image ---
    image_id = None
    for img in coco.get("images", []):
        if img["file_name"] == img_name:
            image_id = img["id"]
            break
    
    if image_id is None:
        logging.warning(f"Image '{img_name}' not found in COCO file. Cannot save annotations.")
        return

    # --- Remove existing annotations for this image ---
    coco["annotations"] = [ann for ann in coco.get("annotations", []) if ann.get("image_id") != image_id]

    # Build a name -> category_id map from existing categories so we can
    # map in-memory class indices back to the original COCO category ids
    name_to_cid = {}
    for cat in coco.get("categories", []):
        if isinstance(cat, dict):
            nm = cat.get("name") or cat.get("label")
            cid = cat.get("id")
            if nm is not None and cid is not None:
                name_to_cid[str(nm).strip()] = cid

    # --- Add new annotations for this image ---
    # Find the max annotation ID to ensure new IDs are unique
    max_ann_id = max([ann.get("id", 0) for ann in coco.get("annotations", [])], default=0)
    
    for i, box in enumerate(boxes, start=1):
        x, y, w, h, class_id = box
        # class_id is expected to be an index into the provided `classes` list.
        # Prefer to map that class name back to the COCO category id if possible
        cid_to_write = None
        try:
            if isinstance(class_id, int) and 0 <= class_id < len(classes):
                cname = classes[class_id]
                # exact match first
                if cname in name_to_cid:
                    cid_to_write = name_to_cid[cname]
                else:
                    # try normalized matching
                    norm = ''.join(ch for ch in cname.lower() if ch.isalnum() or ch.isspace()).strip()
                    for nm, cid in name_to_cid.items():
                        nm_norm = ''.join(ch for ch in nm.lower() if ch.isalnum() or ch.isspace()).strip()
                        if nm_norm == norm:
                            cid_to_write = cid
                            break
        except Exception:
            cid_to_write = None

        # Fallback: if we couldn't map, use the raw numeric class_id (safe fallback)
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

    with open(path, "w") as f:
        json.dump(coco, f, indent=2)
