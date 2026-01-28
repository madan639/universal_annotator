import os


class ClassManager:
    def __init__(self, path="sample_classes/classes.txt"):
        self.path = path
        # Do not auto-create file here; let the app handle the prompt.
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

    def add_class(self, class_name):
        """Add a new class to the list if it doesn't exist."""
        if class_name and class_name not in self.classes:
            self.classes.append(class_name)

    def save_classes(self):
        """Save current classes to the file path."""
        if not self.path:
            return
        try:
            # We default to saving as TXT as it's the primary format for this file
            if self.path.lower().endswith('.json'):
                import json
                with open(self.path, 'w') as f:
                    json.dump(self.classes, f, indent=2)
            else:
                with open(self.path, 'w') as f:
                    for c in self.classes:
                        f.write(f"{c}\n")
        except Exception:
            pass
