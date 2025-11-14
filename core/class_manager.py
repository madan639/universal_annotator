import os


class ClassManager:
    def __init__(self, path="sample_classes/classes.txt"):
        self.path = path
        if not os.path.exists(path):
            # create parent dir if necessary
            parent = os.path.dirname(path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)
            open(path, "w").write("object\n")
        self.load_classes()

    def load_classes(self):
        # Support multiple formats: txt (one class per line) or json
        if not os.path.exists(self.path):
            self.classes = []
            return

        if self.path.lower().endswith('.json'):
            try:
                import json
                with open(self.path, 'r') as f:
                    data = json.load(f)
                # If file is a list of names
                if isinstance(data, list):
                    self.classes = [str(x) for x in data]
                # If COCO-like categories
                elif isinstance(data, dict) and 'categories' in data:
                    cats = data.get('categories', [])
                    names = []
                    for c in cats:
                        if isinstance(c, dict) and 'name' in c:
                            names.append(str(c['name']))
                    self.classes = names
                else:
                    # Fallback: stringify top-level keys
                    self.classes = [str(x) for x in data] if isinstance(data, (list, dict)) else []
            except Exception:
                # On error, fallback to empty
                self.classes = []
        else:
            # Treat as text file: one class per line
            with open(self.path, 'r') as f:
                self.classes = [l.strip() for l in f if l.strip()]

    def get_classes(self):
        return getattr(self, 'classes', [])

    def set_classes_file(self, path):
        self.path = path
        self.load_classes()
        return self.classes

    def set_classes(self, class_list):
        self.classes = class_list
