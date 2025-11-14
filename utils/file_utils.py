import os,json

def list_images(folder):
    valid_ext = (".jpg", ".jpeg", ".png", ".bmp", ".tiff")
    return sorted([f for f in os.listdir(folder) if f.lower().endswith(valid_ext)])

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def ensure_labels_exist(image_dir, label_dir, fmt):
    ensure_dir(label_dir)
    images = list_images(image_dir)

    if fmt == "TXT":
        for img in images:
            base = os.path.splitext(img)[0]
            label_path = os.path.join(label_dir, base + ".txt")
            if not os.path.exists(label_path):
                open(label_path, "w").close()

    elif fmt == "JSON":
        json_path = os.path.join(label_dir, "annotations.json")
        if not os.path.exists(json_path):
            open(json_path, "w").close()

    elif fmt == "RFDETR":
        coco_path = os.path.join(label_dir, "_annotations.coco.json")
        if not os.path.exists(coco_path):
            json.dump({"images": [], "annotations": [], "categories": []}, open(coco_path, "w"))

    print(f"[INFO] Checked label files for {fmt} in {label_dir}")

# ------------------------------
# Label loaders
# ------------------------------
def load_txt_labels(label_path, img_shape):
    boxes = []
    h, w = img_shape
    with open(label_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            cls, x_c, y_c, bw, bh = map(float, parts)
            x = int((x_c - bw / 2) * w)
            y = int((y_c - bh / 2) * h)
            bw = int(bw * w)
            bh = int(bh * h)
            boxes.append((x, y, bw, bh, int(cls)))
    return boxes

def load_json_labels(json_path, image_name):
    boxes = []
    with open(json_path, "r") as f:
        for line in f:
            data = json.loads(line)
            if image_name in data:
                for obj in data[image_name]:
                    x, y, w, h = obj["bbox"]
                    boxes.append((x, y, w, h, 0))
    return boxes

def load_coco_labels(coco_path, image_name):
    boxes = []
    with open(coco_path, "r") as f:
        coco = json.load(f)
        img_entry = next((i for i in coco.get("images", []) if i["file_name"] == image_name), None)
        if not img_entry:
            return boxes
        img_id = img_entry["id"]
        for ann in coco.get("annotations", []):
            if ann["image_id"] == img_id:
                x, y, w, h = ann["bbox"]
                boxes.append((int(x), int(y), int(w), int(h), ann.get("category_id", 0)))
    return boxes
