"""
JSON Helper - Handles JSON format detection, class discovery, and bbox extraction.

This helper extracts all JSON-specific logic from app_window.py including:
- JSON bbox style detection
- JSON class name key detection  
- Class discovery from JSON files
- Dynamic bbox extraction
"""

import os
import json
import logging
import re
from typing import List, Dict, Set, Any, Optional, Tuple


class JSONHelper:
    """Helper class for JSON annotation processing."""
    
    def __init__(self):
        """Initialize the JSON helper."""
        # Include both camelCase and snake_case variants
        self.json_name_keys = ['className', 'class_name', 'category_name', 'name', 'label', 'class']
        self.json_bbox_methods = ['contour', 'bbox', 'points', 'xywh']
    
    def detect_json_bbox_style(self, folder_path: str, sample_limit: int = 20) -> Tuple[List[str], Optional[Dict[int, str]]]:
        """
        Inspect sample JSON files and return prioritized list of bbox styles found plus COCO category map.
        
        Args:
            folder_path: Path to folder containing JSON files
            sample_limit: Maximum number of files to sample
            
        Returns:
            Tuple of (List of bbox styles, Optional COCO category map {id: name})
        """
        if not os.path.isdir(folder_path):
            return ['contour', 'bbox', 'points', 'xywh'], None
        
        files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        files = files[:sample_limit]
        
        style_counts = {
            'contour': 0,
            'bbox': 0,
            'points': 0,
            'xywh': 0
        }
        
        coco_map = {}
        
        def inspect_obj(o):
            """Recursively inspect object for bbox keys."""
            if isinstance(o, dict):
                if 'contour' in o and isinstance(o['contour'], dict) and 'points' in o['contour']:
                    style_counts['contour'] += 1
                if 'bbox' in o:
                    style_counts['bbox'] += 1
                if 'points' in o and isinstance(o['points'], list):
                    style_counts['points'] += 1
                if 'x' in o and 'y' in o and 'width' in o and 'height' in o:
                    style_counts['xywh'] += 1
                for v in o.values():
                    inspect_obj(v)
            elif isinstance(o, list):
                for item in o:
                    inspect_obj(item)
        
        for fname in files:
            try:
                with open(os.path.join(folder_path, fname), 'r') as f:
                    data = json.load(f)
                    
                    # Extract COCO categories if present
                    if isinstance(data, dict) and 'categories' in data and isinstance(data['categories'], list):
                        for cat in data['categories']:
                            if isinstance(cat, dict):
                                cid = cat.get('id') or cat.get('category_id')
                                name = cat.get('name') or cat.get('label')
                                if cid is not None and name:
                                    try:
                                        coco_map[int(cid)] = str(name)
                                    except Exception:
                                        pass
                                        
                    inspect_obj(data)
            except Exception:
                continue
        
        # Sort by count descending
        sorted_styles = sorted(style_counts.items(), key=lambda x: x[1], reverse=True)
        styles = [s[0] for s in sorted_styles if s[1] > 0] or ['contour', 'bbox', 'points', 'xywh']
        
        return styles, (coco_map if coco_map else None)
    
    def detect_json_name_keys(self, folder_path: str, sample_limit: int = 20) -> List[str]:
        """
        Inspect sample JSON files and return ordered list of likely name keys.
        
        Args:
            folder_path: Path to folder containing JSON files
            sample_limit: Maximum number of files to sample
            
        Returns:
            List of probable class name keys ordered by frequency
        """
        if not os.path.isdir(folder_path):
            return ['className', 'category_name', 'name', 'label']
        
        files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        files = files[:sample_limit]
        
        key_counts = {}
        nested_counts = {}  # For nested keys like 'category.name'
        
        def inspect_obj(o):
            """Recursively inspect object for string-valued keys."""
            if isinstance(o, dict):
                for k, v in o.items():
                    if isinstance(v, str) and len(v) < 50:  # Likely a class name
                        key_counts[k] = key_counts.get(k, 0) + 1
                    elif isinstance(v, dict) and 'name' in v:
                        # Nested structure like category: {name: "car"}
                        nested_key = f"{k}.name"
                        nested_counts[nested_key] = nested_counts.get(nested_key, 0) + 1
                    inspect_obj(v)
            elif isinstance(o, list):
                for item in o:
                    inspect_obj(item)
        
        for fname in files:
            try:
                with open(os.path.join(folder_path, fname), 'r') as f:
                    data = json.load(f)
                    inspect_obj(data)
            except Exception:
                continue
        
        # Combine and sort
        all_keys = {**key_counts, **nested_counts}
        sorted_keys  = sorted(all_keys.items(), key=lambda x: x[1], reverse=True)
        result = [k[0] for k in sorted_keys if k[1] > 0]
        
        # Ensure common keys are present
        defaults = ['className', 'category_name', 'name', 'label']
        for default in defaults:
            if default not in result:
                result.append(default)
        
        return result[:10]  # Return top 10
    
    def discover_classes_in_json_folder(self, folder_path: str, name_keys: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Discover unique class names from JSON files.
        
        Args:
            folder_path: Path to folder containing JSON files
            name_keys: List of keys to check for class names
            
        Returns:
            Dictionary mapping class names to occurrence counts
        """
        if name_keys is None:
            name_keys = self.json_name_keys
        
        if not os.path.isdir(folder_path):
            return {}
        
        discovered = {}
        
        def add_count(name):
            """Add or increment count for a class name."""
            if name and isinstance(name, str):
                normalized = name.strip()
                if normalized and not self.looks_like_id(normalized):
                    discovered[normalized] = discovered.get(normalized, 0) + 1
        
        def extract_name(obj):
            """Extract class name from object using configured keys."""
            if not isinstance(obj, dict):
                return None
            
            for key in name_keys:
                if '.' in key:
                    # Handle nested keys like 'category.name'
                    parts = key.split('.')
                    val = obj
                    for part in parts:
                        if isinstance(val, dict) and part in val:
                            val = val[part]
                        else:
                            val = None
                            break
                    if val and isinstance(val, str):
                        return val
                elif key in obj:
                    val = obj[key]
                    if isinstance(val, str):
                        return val
            return None
        
        def inspect_obj(o):
            """Recursively inspect object for class names."""
            if isinstance(o, dict):
                name = extract_name(o)
                if name:
                    add_count(name)
                for v in o.values():
                    inspect_obj(v)
            elif isinstance(o, list):
                for item in o:
                    inspect_obj(item)
        
        files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        for fname in files[:100]:  # Limit to 100 files for performance
            try:
                with open(os.path.join(folder_path, fname), 'r') as f:
                    data = json.load(f)
                    inspect_obj(data)
            except Exception as e:
                logging.debug(f"Error reading {fname}: {e}")
                continue
        
        return discovered
    
    def get_name_from_object(self, obj: Dict[str, Any], name_keys: Optional[List[str]] = None) -> Optional[str]:
        """
        Extract class name from JSON object using configured name keys.
        
        Args:
            obj: JSON object (dict)
            name_keys: List of keys to check (uses default if None)
            
        Returns:
            Extracted class name or None
        """
        if not isinstance(obj, dict):
            return None
        
        if name_keys is None:
            name_keys = self.json_name_keys
        
        for key in name_keys:
            if '.' in key:
                # Handle nested keys
                parts = key.split('.')
                val = obj
                for part in parts:
                    if isinstance(val, dict) and part in val:
                        val = val[part]
                    else:
                        val = None
                        break
                if val and isinstance(val, str):
                    return val
            elif key in obj:
                val = obj[key]
                if isinstance(val, str):
                    return val
        
        return None
    
    @staticmethod
    def normalize_label(name: str) -> str:
        """
        Normalize a label for fuzzy matching.
        
        Args:
            name: Label to normalize
            
        Returns:
            Normalized string (lower, stripped, no punctuation, collapsed spaces)
        """
        if not name:
            return ""
        # Lower, strip, remove punctuation, collapse spaces
        normalized = name.lower().strip()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized
    
    @staticmethod
    def looks_like_id(s: str) -> bool:
        """
        Check if string looks like an opaque ID/UUID rather than a human label.
        
        Args:
            s: String to check
            
        Returns:
            True if looks like an ID, False otherwise
        """
        if not s or not isinstance(s, str):
            return False
        
        # UUID pattern
        if re.match(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', s):
            return True
        
        # Long hex with dashes
        if '-' in s and len(s) > 15:
            parts = s.split('-')
            if all(all(c in '0123456789abcdefABCDEF' for c in p) for p in parts):
                return True
        
        # Very long strings with mostly hex chars
        if len(s) > 20:
            hex_count = sum(1 for c in s if c in '0123456789abcdefABCDEF')
            if hex_count / len(s) > 0.7:
                return True
        
    def extract_bbox(self, obj: Dict[str, Any]) -> Optional[Tuple[float, float, float, float]]:
        """
        Extract bounding box (x, y, w, h) from a JSON object.
        Supports:
        - contour.points (CCTV style)
        - bbox [x, y, w, h] (COCO/standard)
        - bbox {x_min, y_min, x_max, y_max} (min/max style)
        - points list
        
        Returns:
            Tuple (x, y, w, h) in absolute coordinates if found, else None
        """
        if not isinstance(obj, dict):
            return None
            
        # 1. CCTV contour -> points
        if "contour" in obj and isinstance(obj["contour"], dict) and "points" in obj["contour"]:
            pts = obj["contour"]["points"]
            if isinstance(pts, list) and len(pts) >= 2:
                xs = [p.get("x") for p in pts if isinstance(p, dict) and "x" in p]
                ys = [p.get("y") for p in pts if isinstance(p, dict) and "y" in p]
                if xs and ys:
                    x1, x2 = min(xs), max(xs)
                    y1, y2 = min(ys), max(ys)
                    return (x1, y1, abs(x2 - x1), abs(y2 - y1))
        
        # 2. Standard bbox [x, y, w, h] (COCO format)
        if "bbox" in obj and isinstance(obj["bbox"], list) and len(obj["bbox"]) == 4:
            return tuple(obj["bbox"])
        
        # 3. bbox dict with x_min/y_min/x_max/y_max keys
        if "bbox" in obj and isinstance(obj["bbox"], dict):
            bbox = obj["bbox"]
            if all(k in bbox for k in ('x_min', 'y_min', 'x_max', 'y_max')):
                x_min = bbox['x_min']
                y_min = bbox['y_min']
                x_max = bbox['x_max']
                y_max = bbox['y_max']
                return (x_min, y_min, abs(x_max - x_min), abs(y_max - y_min))
            # Also check for xmin/ymin/xmax/ymax (no underscore)
            if all(k in bbox for k in ('xmin', 'ymin', 'xmax', 'ymax')):
                x_min = bbox['xmin']
                y_min = bbox['ymin']
                x_max = bbox['xmax']
                y_max = bbox['ymax']
                return (x_min, y_min, abs(x_max - x_min), abs(y_max - y_min))
            
        # 4. Points list directly in object
        if "points" in obj and isinstance(obj["points"], list) and len(obj["points"]) >= 2:
            pts = obj["points"]
            # Handle list of dicts or list of lists
            xs, ys = [], []
            for p in pts:
                if isinstance(p, dict):
                    if "x" in p: xs.append(p["x"])
                    if "y" in p: ys.append(p["y"])
                elif isinstance(p, (list, tuple)) and len(p) >= 2:
                    xs.append(p[0])
                    ys.append(p[1])
            
            if xs and ys:
                x1, x2 = min(xs), max(xs)
                y1, y2 = min(ys), max(ys)
                return (x1, y1, abs(x2 - x1), abs(y2 - y1))
                
        # 5. xywh keys directly in object
        if all(k in obj for k in ('x', 'y', 'width', 'height')):
             return (obj['x'], obj['y'], obj['width'], obj['height'])

        return None

    def extract_polygon_points(self, obj: Dict[str, Any]) -> Optional[List[Tuple[float, float]]]:
        """
        Extract polygon points from a JSON object.
        Returns List[(x, y)] or None if no polygon found.
        """
        if not isinstance(obj, dict):
            return None
        
        # 1. contour (List of lists or Dict with points)
        if "contour" in obj:
            c = obj["contour"]
            if isinstance(c, list):
                # [[x,y], [x,y]]
                try:
                    return [(float(p[0]), float(p[1])) for p in c if len(p) >= 2]
                except: pass
            elif isinstance(c, dict) and "points" in c:
                 # {"points": [{"x":1,"y":2}, ...]}
                 pts = c["points"]
                 if isinstance(pts, list):
                     try:
                         return [(float(p["x"]), float(p["y"])) for p in pts if "x" in p and "y" in p]
                     except: pass
        
        # 2. points (List of dicts or lists)
        if "points" in obj and isinstance(obj["points"], list):
             pts = obj["points"]
             try:
                 # Check first item to determine format
                 if pts and isinstance(pts[0], dict):
                      return [(float(p["x"]), float(p["y"])) for p in pts if "x" in p and "y" in p]
                 elif pts and isinstance(pts[0], (list, tuple)):
                      return [(float(p[0]), float(p[1])) for p in pts if len(p) >= 2]
             except: pass
        
        # 3. segmentation (COCO style - list of lists, usu. flattenned)
        if "segmentation" in obj:
             seg = obj["segmentation"]
             if isinstance(seg, list) and seg:
                 # [[x,y,x,y...]] (COCO usually has list of polygons)
                 # We take the first one or merge? Typically one object = one polygon (or multipolygon).
                 # For now, take largest if multiple, or just first.
                 # Actually, COCO segmentation is [ [x1,y1,x2,y2,...] ]
                 poly = seg[0]
                 if len(poly) >= 6: # At least 3 points
                     return [(poly[i], poly[i+1]) for i in range(0, len(poly), 2)]
        
        return None
