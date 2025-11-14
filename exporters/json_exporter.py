import os, json

def save_json(export_dir, img_name, boxes, class_name):
    """Saves annotations for a single image to its own JSON file."""
    json_path = os.path.join(export_dir, os.path.splitext(img_name)[0] + ".json")
    
    annotations = []
    for x, y, w, h, class_id in boxes:
        annotations.append({
            "bbox": [x, y, w, h],
            "category_id": int(class_id)
        })

    data = {
        "image": img_name,
        "annotations": annotations
    }

    # Overwrite the file with the new annotations
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
