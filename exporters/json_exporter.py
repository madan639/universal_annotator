import os, json

def save_json(export_dir, img_name, boxes, class_name, polygons=None):
    """Saves annotations for a single image to its own JSON file."""
    json_path = os.path.join(export_dir, os.path.splitext(img_name)[0] + ".json")
    
    formatted_objects = []
    
    # Add BBoxes
    for x, y, w, h, class_id in boxes:
        formatted_objects.append({
            "label": "class_" + str(class_id), # Ideally use real names if available
            "bbox": [x, y, w, h],
            "classId": int(class_id)
        })

    # Add Polygons
    if polygons:
        for pts, class_id in polygons:
            # Convert list of tuples to list of lists [ [x,y], ... ]
            contour = [[float(p[0]), float(p[1])] for p in pts]
            formatted_objects.append({
                "label": "class_" + str(class_id),
                "contour": contour,
                "classId": int(class_id)
            })

    data = {
        "image": img_name,
        "frameName": img_name, # Alias for CCTV format compatibility
        "annotations": formatted_objects, # Standard-ish
        "objects": formatted_objects # CCTV format compatibility
    }

    # Overwrite the file with the new annotations
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
