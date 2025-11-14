import os
import json
from PIL import Image
from tqdm import tqdm

def convert_txt_to_coco(images_folder, txt_folder, output_path=None, class_names=None):
    """
    Converts TXT-format annotations to COCO format with _annotations.coco.json.
    Works with a single dataset (no train/valid/test splits).

    Args:
        images_folder (str): Folder containing images.
        txt_folder (str): Folder containing TXT annotation files.
        output_path (str): Optional output file path for _annotations.coco.json. If None, creates in 'converted_coco_json' folder.
        class_names (list[str]): List of class names.

    Returns:
        dict: Summary with valid_images, skipped, and annotations count.
    """
    # Create default output path if not specified
    if output_path is None:
        output_path = os.path.join(txt_folder, "converted_coco_json", "_annotations.coco.json")
    
    if not class_names:
        class_names = []

    print(f"\n🚀 Converting TXT → COCO: {txt_folder}")

    # Get image files
    image_files = sorted([f for f in os.listdir(images_folder)
                         if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff"))])
    
    if not image_files:
        raise FileNotFoundError(f"No images found in {images_folder}")

    images = []
    annotations = []
    categories = [{"id": i, "name": name, "supercategory": "none"} for i, name in enumerate(class_names)]

    ann_id = 1
    image_id = 1
    skipped_count = 0

    for img_name in tqdm(image_files, desc="Processing images"):
        img_path = os.path.join(images_folder, img_name)
        label_path = os.path.join(txt_folder, os.path.splitext(img_name)[0] + ".txt")

        # Missing label → skip
        if not os.path.exists(label_path):
            skipped_count += 1
            continue

        # Load image
        try:
            with Image.open(img_path) as im:
                w, h = im.size
        except Exception as e:
            print(f"⚠️ Skipping {img_name}: cannot read image ({e})")
            skipped_count += 1
            continue

        # Read labels
        try:
            with open(label_path) as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
        except Exception as e:
            print(f"⚠️ Skipping {img_name}: cannot read labels ({e})")
            skipped_count += 1
            continue

        if not lines:
            skipped_count += 1
            continue

        valid_boxes = 0

        for line in lines:
            parts = line.split()
            if len(parts) != 5:
                continue

            try:
                class_id, xc, yc, bw, bh = map(float, parts)
                class_id = int(class_id)

                # Skip invalids
                if class_id < 0 or class_id >= len(class_names):
                    continue
                if not (0 <= xc <= 1 and 0 <= yc <= 1 and 0 < bw <= 1 and 0 < bh <= 1):
                    continue

                # Convert to absolute xywh
                x = (xc - bw / 2) * w
                y = (yc - bh / 2) * h
                w_box = bw * w
                h_box = bh * h

                if x < 0 or y < 0 or w_box <= 0 or h_box <= 0:
                    continue
                if x + w_box > w or y + h_box > h:
                    continue

                annotations.append({
                    "id": ann_id,
                    "image_id": image_id,
                    "category_id": class_id,
                    "bbox": [x, y, w_box, h_box],
                    "area": w_box * h_box,
                    "iscrowd": 0
                })
                ann_id += 1
                valid_boxes += 1
            except Exception as e:
                print(f"⚠️ Skipping annotation in {img_name}: {str(e)}")
                continue

        if valid_boxes == 0:
            skipped_count += 1
            continue

        images.append({
            "id": image_id,
            "file_name": img_name,
            "width": w,
            "height": h
        })
        image_id += 1

    # Save COCO JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    coco_dict = {
        "info": {"description": "Converted from TXT format"},
        "licenses": [],
        "images": images,
        "annotations": annotations,
        "categories": categories
    }

    with open(output_path, "w") as f:
        json.dump(coco_dict, f, indent=2)

    print(f"\n COCO file created: {output_path}")
    print(f"Images: {len(images)} | Annotations: {len(annotations)} | Categories: {len(categories)}")

    return {
        "valid_images": len(images),
        "skipped": skipped_count,
        "annotations": len(annotations)
    }
