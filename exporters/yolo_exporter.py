import os

def save_txt(export_dir, img_name, boxes):
    txt_path = os.path.join(export_dir, img_name.rsplit('.', 1)[0] + ".txt")
    with open(txt_path, "w") as f:
        for x, y, w, h in boxes:
            # Dummy normalization for example — adapt to actual image dimensions
            f.write(f"0 {x/640:.6f} {y/480:.6f} {w/640:.6f} {h/480:.6f}\n")
