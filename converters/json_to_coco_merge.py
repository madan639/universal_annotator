import os
import json
from PIL import Image
from tqdm import tqdm

def convert_json_folder_to_coco(json_folder, images_folder, output_path=None, class_names=None):
    """
    Converts multiple per-image JSON annotation files into a single COCO-format JSON.
    Output file is created inside a 'converted_coco_json' folder by default.
    
    Supports:
    - bbox annotations (list [x,y,w,h])
    - bbox annotations (dict {x_min, y_min, x_max, y_max})
    - contour/polygon annotations (list of [x,y] points)
    - contour annotations (dict with points [{x, y}])

    Args:
        json_folder (str): Folder containing per-image JSON files.
        images_folder (str): Folder containing images.
        output_path (str): Optional output file path for _annotations.coco.json. If None, creates in 'converted_coco_json' folder.
        class_names (list[str], optional): Class names for the categories list.
    """
    # Create default output path if not specified
    if output_path is None:
        output_path = os.path.join(json_folder, "converted_coco_json", "_annotations.coco.json")
    
    if class_names is None:
        class_names = []

    print(f"\n Converting JSON folder → COCO: {json_folder}")

    # Get JSON files from the specified folder
    json_files = sorted([f for f in os.listdir(json_folder) if f.endswith(".json") and not f.startswith("_")])
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {json_folder}")

    images = []
    annotations = []
    categories = [{"id": i, "name": name, "supercategory": "none"} for i, name in enumerate(class_names)]
    
    # Track dynamically discovered categories
    known_cat_names = {name: i for i, name in enumerate(class_names)}

    image_id = 1
    ann_id = 1

    def _extract_bbox(ann):
        """Extract bbox [x, y, w, h] from various formats."""
        if "bbox" in ann:
            bbox = ann["bbox"]
            if isinstance(bbox, list) and len(bbox) == 4:
                return bbox
            elif isinstance(bbox, dict):
                if all(k in bbox for k in ('x_min', 'y_min', 'x_max', 'y_max')):
                    x_min = bbox['x_min']
                    y_min = bbox['y_min']
                    w = bbox['x_max'] - x_min
                    h = bbox['y_max'] - y_min
                    return [x_min, y_min, w, h]
                if all(k in bbox for k in ('xmin', 'ymin', 'xmax', 'ymax')):
                    x_min = bbox['xmin']
                    y_min = bbox['ymin']
                    w = bbox['xmax'] - x_min
                    h = bbox['ymax'] - y_min
                    return [x_min, y_min, w, h]
        return None

    def _extract_polygon(ann):
        """Extract polygon points as flat list [x1,y1,x2,y2,...] for COCO segmentation."""
        contour = ann.get("contour")
        if contour is not None:
            if isinstance(contour, list):
                # [[x,y], [x,y], ...]
                flat = []
                for p in contour:
                    if isinstance(p, (list, tuple)) and len(p) >= 2:
                        flat.extend([float(p[0]), float(p[1])])
                    elif isinstance(p, dict) and "x" in p and "y" in p:
                        flat.extend([float(p["x"]), float(p["y"])])
                if len(flat) >= 6:  # At least 3 points
                    return flat
            elif isinstance(contour, dict) and "points" in contour:
                pts = contour["points"]
                flat = []
                for p in pts:
                    if isinstance(p, dict) and "x" in p and "y" in p:
                        flat.extend([float(p["x"]), float(p["y"])])
                    elif isinstance(p, (list, tuple)) and len(p) >= 2:
                        flat.extend([float(p[0]), float(p[1])])
                if len(flat) >= 6:
                    return flat

        # Also check "points" directly
        points = ann.get("points")
        if points and isinstance(points, list):
            flat = []
            for p in points:
                if isinstance(p, dict) and "x" in p and "y" in p:
                    flat.extend([float(p["x"]), float(p["y"])])
                elif isinstance(p, (list, tuple)) and len(p) >= 2:
                    flat.extend([float(p[0]), float(p[1])])
            if len(flat) >= 6:
                return flat

        # Check "segmentation"
        seg = ann.get("segmentation")
        if seg and isinstance(seg, list) and seg:
            if isinstance(seg[0], list) and len(seg[0]) >= 6:
                return seg[0]

        return None

    def _resolve_category_id(ann):
        """Resolve category ID, creating new categories as needed."""
        nonlocal categories

        # Try to get class name first
        cls_name = ann.get("className") or ann.get("class_name") or ann.get("label")
        cls_id = ann.get("classId", ann.get("category_id", ann.get("class_id", None)))

        # If we have a proper class name
        if cls_name and isinstance(cls_name, str):
            import re
            # Skip generic names like "class_0"
            if not re.match(r'^class_\d+$', cls_name, re.IGNORECASE):
                if cls_name in known_cat_names:
                    return known_cat_names[cls_name]
                else:
                    new_id = len(categories)
                    categories.append({"id": new_id, "name": cls_name, "supercategory": "none"})
                    known_cat_names[cls_name] = new_id
                    return new_id

        # Fall back to classId
        if cls_id is not None:
            cls_id = int(cls_id)
            # Check if this ID is within known categories
            if cls_id < len(categories):
                return cls_id
            else:
                # Create placeholder
                placeholder = f"class_{cls_id}"
                if placeholder not in known_cat_names:
                    new_id = len(categories)
                    categories.append({"id": new_id, "name": placeholder, "supercategory": "none"})
                    known_cat_names[placeholder] = new_id
                    return new_id
                return known_cat_names[placeholder]

        return 0

    def _bbox_from_polygon(flat_seg):
        """Compute bbox [x,y,w,h] from flat segmentation points."""
        xs = flat_seg[0::2]
        ys = flat_seg[1::2]
        x_min = min(xs)
        y_min = min(ys)
        return [x_min, y_min, max(xs) - x_min, max(ys) - y_min]

    def _process_annotations(data_item):
        """Process annotations from a JSON item (dict)."""
        nonlocal ann_id, image_id

        img_name = data_item.get("image") or data_item.get("frameName")
        if not img_name:
            return
        img_path = os.path.join(images_folder, img_name)

        # Get image size
        try:
            with Image.open(img_path) as im:
                w, h = im.size
        except Exception as e:
            print(f"  Skipping {img_name}: cannot open ({e})")
            return

        # Add image entry
        images.append({
            "id": image_id,
            "file_name": img_name,
            "width": w,
            "height": h
        })

        # Get annotation objects
        ann_list = data_item.get("annotations", []) or data_item.get("objects", [])

        for ann in ann_list:
            if not isinstance(ann, dict):
                continue

            category_id = _resolve_category_id(ann)

            # Try polygon/contour first, then bbox
            poly_flat = _extract_polygon(ann)
            bbox = _extract_bbox(ann)

            if poly_flat:
                # Polygon annotation
                if not bbox:
                    bbox = _bbox_from_polygon(poly_flat)
                area = bbox[2] * bbox[3] if bbox else 0

                annotations.append({
                    "id": ann_id,
                    "image_id": image_id,
                    "category_id": category_id,
                    "segmentation": [poly_flat],
                    "bbox": bbox,
                    "area": area,
                    "iscrowd": 0
                })
                ann_id += 1

            elif bbox:
                # BBox-only annotation
                x, y, bw, bh = bbox
                annotations.append({
                    "id": ann_id,
                    "image_id": image_id,
                    "category_id": category_id,
                    "bbox": [x, y, bw, bh],
                    "area": bw * bh,
                    "iscrowd": 0
                })
                ann_id += 1

        image_id += 1

    for json_file in tqdm(json_files, desc="Processing JSON files"):
        json_path = os.path.join(json_folder, json_file)

        try:
            with open(json_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  Skipping {json_file}: {str(e)}")
            continue

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    _process_annotations(item)
        elif isinstance(data, dict):
            _process_annotations(data)

    coco_dict = {
        "info": {"description": "Combined COCO dataset from per-image JSONs"},
        "licenses": [],
        "images": images,
        "annotations": annotations,
        "categories": categories
    }

    # Create output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(coco_dict, f, indent=2)

    print(f"\n COCO file created: {output_path}")
    print(f"Images: {len(images)} | Annotations: {len(annotations)} | Categories: {len(categories)}")

    return {
        "images": len(images),
        "annotations": len(annotations),
        "categories": len(categories)
    }
