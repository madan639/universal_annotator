import os
import json
from PIL import Image
from tqdm import tqdm

def convert_json_folder_to_coco(json_folder, images_folder, output_path=None, class_names=None):
    """
    Converts multiple per-image JSON annotation files into a single COCO-format JSON.
    Output file is created inside a 'converted_coco_json' folder by default.

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

    print(f"\n🚀 Converting JSON folder → COCO: {json_folder}")

    # Get JSON files from the specified folder
    json_files = sorted([f for f in os.listdir(json_folder) if f.endswith(".json") and not f.startswith("_")])
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {json_folder}")

    images = []
    annotations = []
    categories = [{"id": i, "name": name, "supercategory": "none"} for i, name in enumerate(class_names)]

    image_id = 1
    ann_id = 1

    for json_file in tqdm(json_files, desc="Processing JSON files"):
        json_path = os.path.join(json_folder, json_file)

        try:
            with open(json_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"⚠️ Skipping {json_file}: {str(e)}")
            continue

        # Handle both list and dict formats
        if isinstance(data, list):
            # If it's a list, process each item
            for item in data:
                if isinstance(item, dict):
                    img_name = item.get("image") or os.path.splitext(json_file)[0] + ".jpg"
                    img_path = os.path.join(images_folder, img_name)

                    # Get image size
                    try:
                        with Image.open(img_path) as im:
                            w, h = im.size
                    except Exception as e:
                        print(f"⚠️ Skipping {img_name}: cannot open ({e})")
                        continue

                    # Add image entry
                    images.append({
                        "id": image_id,
                        "file_name": img_name,
                        "width": w,
                        "height": h
                    })

                    # Add annotation entries
                    for ann in item.get("annotations", []):
                        if "bbox" not in ann:
                            continue

                        bbox = ann["bbox"]
                        if len(bbox) != 4:
                            continue

                        category_id = ann.get("category_id", 0)
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
        else:
            # If it's a dict, process normally
            img_name = data.get("image") or os.path.splitext(json_file)[0] + ".jpg"
            img_path = os.path.join(images_folder, img_name)

            # Get image size
            try:
                with Image.open(img_path) as im:
                    w, h = im.size
            except Exception as e:
                print(f"⚠️ Skipping {img_name}: cannot open ({e})")
                continue

            # Add image entry
            images.append({
                "id": image_id,
                "file_name": img_name,
                "width": w,
                "height": h
            })

            # Add annotation entries
            for ann in data.get("annotations", []):
                if "bbox" not in ann:
                    continue

                bbox = ann["bbox"]
                if len(bbox) != 4:
                    continue

                category_id = ann.get("category_id", 0)
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
