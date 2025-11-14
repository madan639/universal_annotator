import os
import sys
import json
import logging
import cv2


def load_class_map(base_path):
    """Load classes.txt mapping className -> txt ID."""
    candidates = [
        os.path.join(base_path, "classes.txt"),
        os.path.join(os.path.dirname(base_path), "classes.txt"),
        os.path.join(os.getcwd(), "sample_classes", "classes.txt")
    ]

    for c in candidates:
        if os.path.exists(c):
            with open(c) as f:
                names = [x.strip() for x in f.readlines() if x.strip()]
            return {name: i for i, name in enumerate(names)}

    return {}  # fallback (will cause class skip)


def write_txt(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines))
    logging.info(f"Saved {path} ({len(lines)} boxes)")


def convert_json_to_txt(input_path, output_dir=None, image_dir=None, class_map=None, interactive=True):
    """
    Master entry point — supports:
    - CCTV JSON (your format)
    - folder of CCTV JSONs
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(input_path), "converted_txt")

    os.makedirs(output_dir, exist_ok=True)

    class_map = class_map or load_class_map(input_path)

    # If no class_map found, attempt to discover class names from the JSON(s).
    if not class_map:
        logging.info("No classes.txt found — attempting to discover class names from JSON annotations.")
        discovered = []

        def collect_from_data(data_obj):
            if not isinstance(data_obj, dict):
                return
            for o in data_obj.get('objects', []):
                nm = o.get('className')
                if nm:
                    discovered.append(nm)

        if os.path.isdir(input_path):
            for fn in os.listdir(input_path):
                if not fn.endswith('.json'):
                    continue
                p = os.path.join(input_path, fn)
                try:
                    with open(p) as f:
                        d = json.load(f)
                except Exception:
                    continue
                if isinstance(d, list):
                    for el in d:
                        collect_from_data(el)
                else:
                    collect_from_data(d)
        else:
            try:
                with open(input_path) as f:
                    d = json.load(f)
            except Exception:
                d = None
            if isinstance(d, list):
                for el in d:
                    collect_from_data(el)
            else:
                collect_from_data(d)

        discovered_unique = list(dict.fromkeys(discovered))  # preserve order

        if not discovered_unique:
            logging.warning("⚠ No className values discovered in JSON files; class_map remains empty and objects may be skipped.")
        else:
            # Prepare classes.txt path next to input (folder) or in same dir as file
            save_dir = input_path if os.path.isdir(input_path) else os.path.dirname(input_path)
            classes_path = os.path.join(save_dir, 'classes.txt')

            # if running in a non-interactive environment, don't attempt to prompt
            if interactive and not sys.stdin.isatty():
                logging.info("Non-interactive session detected; falling back to automatic classes.txt creation.")
                interactive = False

            if interactive:
                print("Detected class names in JSON files:")
                for i, name in enumerate(discovered_unique):
                    print(f"  [{i}] {name}")
                print("\nYou can accept the default ordering (0..N-1), or provide explicit numeric ids.")
                print("Enter mappings in the form 'name:id' separated by commas (e.g. 'person:0,helmet:1'), or press Enter to accept default ordering.")
                user_input = input("Mappings: ").strip()

                name_to_id = {}
                if user_input:
                    parts = [p.strip() for p in user_input.split(',') if p.strip()]
                    for p in parts:
                        if ':' not in p:
                            print(f"Skipping invalid mapping '{p}'")
                            continue
                        nm, sid = p.split(':', 1)
                        nm = nm.strip()
                        try:
                            sidv = int(sid.strip())
                        except Exception:
                            print(f"Invalid id for '{nm}': '{sid}'. Skipping.")
                            continue
                        name_to_id[nm] = sidv

                if name_to_id:
                    # build ordered list according to provided ids and fill gaps
                    max_id = max(name_to_id.values())
                    ordered = [None] * (max_id + 1)
                    remaining = [n for n in discovered_unique if n not in name_to_id]
                    for nm, sid in name_to_id.items():
                        if sid < 0:
                            continue
                        if sid < len(ordered) and ordered[sid] is None:
                            ordered[sid] = nm
                        else:
                            # collision or out-of-range: append later
                            remaining.append(nm)
                    ri = 0
                    for idx in range(len(ordered)):
                        if ordered[idx] is None and ri < len(remaining):
                            ordered[idx] = remaining[ri]
                            ri += 1
                    while ri < len(remaining):
                        ordered.append(remaining[ri])
                        ri += 1
                    final_names = [n for n in ordered if n is not None]
                else:
                    final_names = discovered_unique

                try:
                    with open(classes_path, 'w') as cf:
                        for n in final_names:
                            cf.write(n + '\n')
                    logging.info(f"Created classes.txt with {len(final_names)} classes at {classes_path}")
                    class_map = {name: i for i, name in enumerate(final_names)}
                except Exception:
                    logging.warning("Failed to write classes.txt; proceeding with discovered ordering in-memory")
                    class_map = {name: i for i, name in enumerate(discovered_unique)}
            else:
                try:
                    with open(classes_path, 'w') as cf:
                        for n in discovered_unique:
                            cf.write(n + '\n')
                    logging.info(f"Auto-created classes.txt with {len(discovered_unique)} classes at {classes_path}")
                    class_map = {name: i for i, name in enumerate(discovered_unique)}
                except Exception:
                    logging.warning("Failed to write auto-generated classes.txt; proceeding with discovered ordering in-memory")
                    class_map = {name: i for i, name in enumerate(discovered_unique)}

    # --------------------------
    # Folder mode
    # --------------------------
    if os.path.isdir(input_path):
        json_files = [f for f in os.listdir(input_path) if f.endswith(".json")]
        for jf in json_files:
            convert_single_json(
                os.path.join(input_path, jf),
                output_dir,
                image_dir,
                class_map,
            )
        return

    # --------------------------
    # Single JSON file mode
    # --------------------------
    convert_single_json(input_path, output_dir, image_dir, class_map)


def convert_single_json(json_path, output_dir, image_dir, class_map):
    """Convert a single CCTV JSON annotation."""

    try:
        with open(json_path) as f:
            data = json.load(f)
    except:
        logging.error(f"❌ Cannot parse {json_path}")
        return

    # CASE 1: JSON is a list → pick first element
    if isinstance(data, list):
        if len(data) == 0 or not isinstance(data[0], dict):
            logging.error(f"❌ JSON list invalid: {json_path}")
            return
        data = data[0]  # <-- FIXED HERE

    # Now data MUST be a dict
    if not isinstance(data, dict):
        logging.warning(f"⚠ Unknown JSON shape in {json_path}")
        return

    # Detect CCTV format
    if "objects" in data and ("frameName" in data or "image" in data):
        convert_cctv(data, json_path, output_dir, image_dir, class_map)
    else:
        logging.warning(f"⚠ Unknown JSON format: {json_path}")


def convert_cctv(data, json_path, output_dir, image_dir, class_map):
    """Convert your CCTV JSON (now supports list-wrapped JSON)."""

    # -----------------------------
    # Extract image filename
    # -----------------------------

    img_key_candidates = ["frameName", "image", "filename", "file"]
    img_name = None

    for k in img_key_candidates:
        if k in data and isinstance(data[k], str):
            img_name = os.path.basename(data[k])
            break

    if not img_name:
        # fallback
        img_name = os.path.splitext(os.path.basename(json_path))[0] + ".jpg"

    img_base = os.path.splitext(img_name)[0]

    # -----------------------------
    # Image size
    # -----------------------------
    width = data.get("width")
    height = data.get("height")

    if (not width or not height) and image_dir:
        img_path = os.path.join(image_dir, img_name)
        if os.path.exists(img_path):
            img = cv2.imread(img_path)
            if img is not None:
                height, width = img.shape[:2]

    if not width or not height:
        logging.error(f"❌ Missing width/height in {json_path}")
        return

    # -----------------------------
    # Extract objects
    # -----------------------------
    out_lines = []

    for obj in data.get("objects", []):

        # ---- Extract box via contour.points ----
        if "contour" in obj and "points" in obj["contour"]:
            pts = obj["contour"]["points"]
            if len(pts) < 2:
                continue

            x1, y1 = pts[0].get("x"), pts[0].get("y")
            x2, y2 = pts[1].get("x"), pts[1].get("y")

            if None in (x1, y1, x2, y2):
                continue

            x = min(x1, x2)
            y = min(y1, y2)
            w = abs(x2 - x1)
            h = abs(y2 - y1)

        else:
            continue

        # ---- Resolve className → txt id (robust matching) ----
        cname = obj.get("className")
        if not cname:
            logging.warning(f"⚠ Missing className for object in {json_path}")
            continue

        cls_id = None
        # direct match
        if cname in class_map:
            cls_id = class_map[cname]
        else:
            # try case-insensitive match against keys
            lname = cname.lower()
            for k, v in class_map.items():
                if k and k.lower() == lname:
                    cls_id = v
                    break

        if cls_id is None:
            logging.warning(f"⚠ Unknown className '{cname}' in {json_path}")
            continue

        # Normalize
        xc = (x + w / 2) / width
        yc = (y + h / 2) / height
        nw = w / width
        nh = h / height

        out_lines.append(f"{cls_id} {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}")

    # Write TXT
    txt_path = os.path.join(output_dir, img_base + ".txt")
    write_txt(txt_path, out_lines)
