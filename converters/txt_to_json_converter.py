import os
import json


def convert_txt_to_json(input_dir, output_dir=None, img_size=None, class_names=None):
    """
    Convert txt format (.txt) labels to JSON format.
    Each txt file is converted into a single JSON file with identical base name.

    Args:
        input_dir (str): Path to directory containing txt .txt label files.
        output_dir (str): Optional path to directory where JSON files will be saved. If None, creates 'converted_json'.
        img_size (tuple): Optional (height, width) for normalization reverse mapping.
        class_names (list): Optional list of class names. Index corresponds to class ID in TXT.
                           If provided, class names will be used instead of generic "class_0".
    """
    # Create default output folder if not specified
    if output_dir is None:
        output_dir = os.path.join(input_dir, "converted_json")
    
    os.makedirs(output_dir, exist_ok=True)
    txt_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]

    if not txt_files:
        raise ValueError("No txt .txt label files found in directory.")

    converted = []

    for file in txt_files:
        input_path = os.path.join(input_dir, file)
        image_name = os.path.splitext(file)[0] + ".jpg"

        annotations = []
        with open(input_path, "r") as f:
            for line in f:
                vals = line.strip().split()
                if len(vals) < 5:
                    continue
                
                cls_id = int(vals[0])
                coords = [float(v) for v in vals[1:]]
                
                # Resolve class name
                if class_names and cls_id < len(class_names):
                    cls_name = class_names[cls_id]
                else:
                    cls_name = f"class_{cls_id}"
                
                # Check for Polygon (more than 4 coords)
                if len(coords) > 4:
                    # It's a polygon
                    points = []
                    for i in range(0, len(coords), 2):
                       if i+1 >= len(coords): break
                       px = coords[i]
                       py = coords[i+1]
                       
                       # De-normalize
                       if img_size:
                           img_h, img_w = img_size
                           px *= img_w
                           py *= img_h
                           
                       points.append([px, py])
                    
                    annotations.append({
                        "contour": points,
                        "classId": cls_id,
                        "className": cls_name,
                        "label": cls_name,
                        "type": "polygon"
                    })
                else: 
                     # It's a BBox
                    xc, yc, bw, bh = coords
                    # De-normalize if image size known
                    if img_size:
                        img_h, img_w = img_size
                        x = (xc - bw / 2) * img_w
                        y = (yc - bh / 2) * img_h
                        w = bw * img_w
                        h = bh * img_h
                    else:
                        x, y, w, h = xc, yc, bw, bh
    
                    annotations.append({
                        "bbox": [x, y, w, h],
                        "classId": cls_id,
                        "className": cls_name,
                        "label": cls_name,
                        "category_id": cls_id,
                        "type": "bbox"
                    })

        json_data = {
            "image": image_name,
            "annotations": annotations
        }

        output_path = os.path.join(output_dir, os.path.splitext(file)[0] + ".json")
        with open(output_path, "w") as jf:
            json.dump(json_data, jf, indent=4)

        converted.append(output_path)

    return converted
