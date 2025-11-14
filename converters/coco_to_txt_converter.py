import os
import json
from tqdm import tqdm

def convert_coco_to_txt(coco_json_path, output_txt_folder=None, classes_txt_path=None):
    """
    Converts a COCO-format JSON file to txt-format .txt annotations.

    Args:
        coco_json_path (str): Path to COCO-format JSON file.
        output_txt_folder (str): Optional folder to save txt .txt annotations. If None, creates in 'converted_txt' folder.
        classes_txt_path (str): Optional path to save classes.txt file. If None, saves in output folder.
    """
    # Create default output folders if not specified
    if output_txt_folder is None:
        output_txt_folder = os.path.join(os.path.dirname(coco_json_path), "converted_txt")
    
    if classes_txt_path is None:
        classes_txt_path = os.path.join(output_txt_folder, "classes.txt")
    # Load COCO JSON
    with open(coco_json_path, 'r') as f:
        coco_data = json.load(f)

    # Prepare output folder
    os.makedirs(output_txt_folder, exist_ok=True)
    os.makedirs(os.path.dirname(classes_txt_path), exist_ok=True)

    # Extract categories
    categories = sorted(coco_data["categories"], key=lambda x: x["id"])
    class_names = [cat["name"] for cat in categories]
    class_id_map = {cat["id"]: i for i, cat in enumerate(categories)}

    # Save classes.txt
    with open(classes_txt_path, "w") as f:
        for name in class_names:
            f.write(name + "\n")

    print(f"✅ Saved classes.txt → {classes_txt_path}")

    # Build lookup for images
    images_info = {img["id"]: img for img in coco_data["images"]}

    # Group annotations by image_id
    image_to_anns = {}
    for ann in coco_data["annotations"]:
        img_id = ann["image_id"]
        if img_id not in image_to_anns:
            image_to_anns[img_id] = []
        image_to_anns[img_id].append(ann)

    # Convert and save txt TXT files
    for img_id, img_info in tqdm(images_info.items(), desc="Converting COCO → txt"):
        img_name = os.path.splitext(img_info["file_name"])[0]
        w, h = img_info["width"], img_info["height"]

        txt_path = os.path.join(output_txt_folder, img_name + ".txt")

        lines = []
        anns = image_to_anns.get(img_id, [])

        for ann in anns:
            cat_id = ann["category_id"]
            if cat_id not in class_id_map:
                continue

            x, y, bw, bh = ann["bbox"]
            # Convert COCO xywh → txt normalized (xc, yc, w, h)
            xc = (x + bw / 2) / w
            yc = (y + bh / 2) / h
            bw /= w
            bh /= h

            # Clamp to [0,1]
            xc = max(0, min(1, xc))
            yc = max(0, min(1, yc))
            bw = max(0, min(1, bw))
            bh = max(0, min(1, bh))

            class_idx = class_id_map[cat_id]
            lines.append(f"{class_idx} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")

        # Write annotation file
        if lines:
            with open(txt_path, "w") as f:
                f.write("\n".join(lines))

    print(f"\n✅ Conversion complete!")
    print(f"Annotations saved in: {output_txt_folder}")
    print(f"Classes saved in: {classes_txt_path}")
