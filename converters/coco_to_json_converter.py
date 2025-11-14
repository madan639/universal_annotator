import os
import json
from tqdm import tqdm

def convert_coco_to_json_folder(coco_json_path, output_json_folder=None, class_txt_path=None):
    """
    Converts a single COCO-format JSON into multiple per-image JSON annotation files.
    Also creates a classes.txt file listing all class names.

    Args:
        coco_json_path (str): Path to the COCO-format JSON file.
        output_json_folder (str): Optional folder to save per-image JSONs. If None, creates in 'converted_json' folder.
        class_txt_path (str): Optional path to save classes.txt file. If None, saves in output folder.
    """
    # Create default output folders if not specified
    if output_json_folder is None:
        output_json_folder = os.path.join(os.path.dirname(coco_json_path), "converted_json")
    
    if class_txt_path is None:
        class_txt_path = os.path.join(output_json_folder, "classes.txt")
    
    print(f"\n🚀 Converting COCO → JSON folder: {coco_json_path}")

    # Load COCO JSON
    with open(coco_json_path, "r") as f:
        coco_data = json.load(f)

    # Prepare output folders
    os.makedirs(output_json_folder, exist_ok=True)
    os.makedirs(os.path.dirname(class_txt_path), exist_ok=True)

    # Extract categories
    categories = sorted(coco_data["categories"], key=lambda x: x["id"])
    class_names = [cat["name"] for cat in categories]
    cat_id_to_name = {cat["id"]: cat["name"] for cat in categories}

    # Save classes.txt
    with open(class_txt_path, "w") as f:
        for name in class_names:
            f.write(name + "\n")
    print(f"✅ Saved classes.txt → {class_txt_path}")

    # Build lookup for images
    images_info = {img["id"]: img for img in coco_data["images"]}

    # Group annotations by image_id
    image_to_anns = {}
    for ann in coco_data["annotations"]:
        img_id = ann["image_id"]
        if img_id not in image_to_anns:
            image_to_anns[img_id] = []
        image_to_anns[img_id].append(ann)

    # Convert each image + its annotations to per-image JSON
    for img_id, img_info in tqdm(images_info.items(), desc="Creating per-image JSONs"):
        img_name = img_info["file_name"]
        w, h = img_info["width"], img_info["height"]

        anns = image_to_anns.get(img_id, [])
        ann_list = []

        for ann in anns:
            bbox = ann.get("bbox", [])
            if len(bbox) != 4:
                continue

            cat_id = ann.get("category_id", 0)
            category_name = cat_id_to_name.get(cat_id, "unknown")

            ann_list.append({
                "category_id": cat_id,
                "category_name": category_name,
                "bbox": bbox
            })

        # Build the JSON object
        image_json = {
            "image": img_name,
            "width": w,
            "height": h,
            "annotations": ann_list
        }

        # Save as a per-image JSON file
        json_output_path = os.path.join(
            output_json_folder, os.path.splitext(img_name)[0] + ".json"
        )
        with open(json_output_path, "w") as f:
            json.dump(image_json, f, indent=2)

    print(f"\n✅ Conversion complete!")
    print(f"Per-image JSONs saved in: {output_json_folder}")
    print(f"Classes saved in: {class_txt_path}")

