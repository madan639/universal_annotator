"""
Comprehensive test suite for annotation format converters.

Tests include:
- json_to_txt conversion with bbox coordinate validation
- txt_to_annotaion_coco_json conversion with bbox coordinate validation
- Edge cases: empty files, missing classes, invalid data
"""

import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path

# Import converters
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from converters.json_to_txt import convert_json_to_txt, convert_single_json, convert_cctv
from converters.txt_to_annotaion_coco_json import convert_txt_to_coco
from converters.txt_to_json_converter import convert_txt_to_json
from converters.json_to_coco_merge import convert_json_folder_to_coco
from converters.coco_to_json_converter import convert_coco_to_json_folder
from converters.coco_to_txt_converter import convert_coco_to_txt


class TestJsonToTxt:
    """Test suite for JSON to TXT conversion"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def sample_json_cctv(self, temp_dir):
        """Create a sample CCTV-format JSON file"""
        data = {
            "frameName": "test_image.jpg",
            "width": 1920,
            "height": 1080,
            "objects": [
                {
                    "className": "person",
                    "contour": {
                        "points": [
                            {"x": 100, "y": 100},
                            {"x": 200, "y": 200}
                        ]
                    }
                },
                {
                    "className": "car",
                    "contour": {
                        "points": [
                            {"x": 500, "y": 500},
                            {"x": 700, "y": 700}
                        ]
                    }
                }
            ]
        }
        json_path = os.path.join(temp_dir, "test_image.json")
        with open(json_path, 'w') as f:
            json.dump(data, f)
        return json_path
    
    @pytest.fixture
    def classes_file(self, temp_dir):
        """Create a classes.txt file"""
        classes_path = os.path.join(temp_dir, "classes.txt")
        with open(classes_path, 'w') as f:
            f.write("person\n")
            f.write("car\n")
        return classes_path
    
    def test_json_to_txt_basic_conversion(self, temp_dir, sample_json_cctv, classes_file):
        """Test basic JSON to TXT conversion with correct bbox coordinates"""
        output_dir = os.path.join(temp_dir, "output_txt")
        
        convert_json_to_txt(
            sample_json_cctv, 
            output_dir=output_dir,
            class_map={"person": 0, "car": 1},
            interactive=False
        )
        
        # Check output file exists
        output_file = os.path.join(output_dir, "test_image.txt")
        assert os.path.exists(output_file), "Output TXT file should be created"
        
        # Read and validate content
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2, "Should have 2 annotations"
        
        # Parse first line (person)
        parts = lines[0].strip().split()
        assert len(parts) == 5, "Each line should have 5 values"
        cls_id, xc, yc, w, h = int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
        
        # Validate class ID
        assert cls_id == 0, "First object should be class 0 (person)"
        
        # Validate normalized coordinates (should be between 0 and 1)
        assert 0 <= xc <= 1, f"xc should be normalized: {xc}"
        assert 0 <= yc <= 1, f"yc should be normalized: {yc}"
        assert 0 < w <= 1, f"w should be normalized: {w}"
        assert 0 < h <= 1, f"h should be normalized: {h}"
        
        # Calculate expected values for person bbox
        # Original: x1=100, y1=100, x2=200, y2=200, image: 1920x1080
        # Expected: x=100, y=100, w=100, h=100
        # Normalized: xc=(100+100/2)/1920=0.078125, yc=(100+100/2)/1080=0.138889, w=100/1920=0.052083, h=100/1080=0.092593
        assert abs(xc - 0.078125) < 0.001, f"Person xc should be ~0.078, got {xc}"
        assert abs(yc - 0.138889) < 0.001, f"Person yc should be ~0.139, got {yc}"
        assert abs(w - 0.052083) < 0.001, f"Person w should be ~0.052, got {w}"
        assert abs(h - 0.092593) < 0.001, f"Person h should be ~0.093, got {h}"
    
    def test_json_to_txt_missing_classes(self, temp_dir):
        """Test JSON to TXT conversion when classes.txt is missing"""
        data = {
            "frameName": "test.jpg",
            "width": 1920,
            "height": 1080,
            "objects": [
                {
                    "className": "dog",
                    "contour": {
                        "points": [
                            {"x": 100, "y": 100},
                            {"x": 200, "y": 200}
                        ]
                    }
                }
            ]
        }
        
        json_path = os.path.join(temp_dir, "test.json")
        with open(json_path, 'w') as f:
            json.dump(data, f)
        
        output_dir = os.path.join(temp_dir, "output")
        
        # Should auto-discover classes
        convert_json_to_txt(json_path, output_dir=output_dir, interactive=False)
        
        # Check classes.txt was created
        classes_path = os.path.join(temp_dir, "classes.txt")
        assert os.path.exists(classes_path), "classes.txt should be auto-created"
        
        with open(classes_path, 'r') as f:
            classes = [line.strip() for line in f.readlines()]
        
        assert "dog" in classes, "Discovered class 'dog' should be in classes.txt"
    
    def test_json_to_txt_empty_objects(self, temp_dir):
        """Test JSON with no objects"""
        data = {
            "frameName": "empty.jpg",
            "width": 1920,
            "height": 1080,
            "objects": []
        }
        
        json_path = os.path.join(temp_dir, "empty.json")
        with open(json_path, 'w') as f:
            json.dump(data, f)
        
        output_dir = os.path.join(temp_dir, "output")
        convert_json_to_txt(json_path, output_dir=output_dir, interactive=False)
        
        # Should create empty txt file
        output_file = os.path.join(output_dir, "empty.txt")
        assert os.path.exists(output_file), "Output file should exist even with no objects"
        
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 0, "File should be empty"


class TestTxtToCoco:
    """Test suite for TXT to COCO conversion"""
    
    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def sample_txt_and_image(self, temp_dir):
        """Create sample TXT annotation and dummy image"""
        # Create dummy image using PIL
        from PIL import Image
        img = Image.new('RGB', (1920, 1080), color='red')
        img_path = os.path.join(temp_dir, "test_image.jpg")
        img.save(img_path)
        
        # Create TXT annotation
        # Format: class_id xc yc w h (normalized)
        txt_path = os.path.join(temp_dir, "test_image.txt")
        with open(txt_path, 'w') as f:
            # Person at center with 100x100 box
            f.write("0 0.5 0.5 0.052083 0.092593\n")
            # Car at another location
            f.write("1 0.7 0.7 0.1 0.1\n")
        
        return temp_dir, img_path, txt_path
    
    def test_txt_to_coco_basic_conversion(self, temp_dir, sample_txt_and_image):
        """Test TXT to COCO conversion with bbox coordinate validation"""
        img_dir, _, _ = sample_txt_and_image
        
        output_path = os.path.join(temp_dir, "_annotations.coco.json")
        class_names = ["person", "car"]
        
        result = convert_txt_to_coco(
            images_folder=img_dir,
            txt_folder=img_dir,
            output_path=output_path,
            class_names=class_names
        )
        
        # Check file exists
        assert os.path.exists(output_path), "COCO JSON should be created"
        
        # Load and validate COCO format
        with open(output_path, 'r') as f:
            coco_data = json.load(f)
        
        assert "images" in coco_data
        assert "annotations" in coco_data
        assert "categories" in coco_data
        
        # Validate structure
        assert len(coco_data["images"]) == 1, "Should have 1 image"
        assert len(coco_data["annotations"]) == 2, "Should have 2 annotations"
        assert len(coco_data["categories"]) == 2, "Should have 2 categories"
        
        # Validate bbox coordinates
        ann = coco_data["annotations"][0]
        bbox = ann["bbox"]
        
        # COCO bbox format: [x, y, width, height] in absolute coordinates
        x, y, w, h = bbox
        
        # Original normalized: xc=0.5, yc=0.5, w=0.052083, h=0.092593
        # Image size: 1920x1080
        # Expected absolute: x=(0.5-0.052083/2)*1920=909.92, y=(0.5-0.092593/2)*1080=489.88
        # w=0.052083*1920=100, h=0.092593*1080=100
        
        assert abs(w - 100) < 1, f"Width should be ~100px, got {w}"
        assert abs(h - 100) < 1, f"Height should be ~100px, got {h}"
        
        # Verify x, y are reasonable
        assert 0 <= x < 1920, f"X coordinate should be within image bounds, got {x}"
        assert 0 <= y < 1080, f"Y coordinate should be within image bounds, got {y}"
    
    def test_txt_to_coco_empty_annotation(self, temp_dir):
        """Test with empty TXT file"""
        from PIL import Image
        
        # Create dummy image
        img = Image.new('RGB', (640, 480), color='blue')
        img_path = os.path.join(temp_dir, "empty.jpg")
        img.save(img_path)
        
        # Create empty TXT
        txt_path = os.path.join(temp_dir, "empty.txt")
        with open(txt_path, 'w') as f:
            f.write("")
        
        output_path = os.path.join(temp_dir, "_annotations.coco.json")
        
        result = convert_txt_to_coco(
            images_folder=temp_dir,
            txt_folder=temp_dir,
            output_path=output_path,
            class_names=["person"]
        )
        
        # Should skip images with no annotations
        with open(output_path, 'r') as f:
            coco_data = json.load(f)
        
        assert len(coco_data["images"]) == 0, "Should skip images with empty annotations"
    
    def test_txt_to_coco_invalid_bbox(self, temp_dir):
        """Test with invalid bbox coordinates"""
        from PIL import Image
        
        img = Image.new('RGB', (640, 480), color='green')
        img_path = os.path.join(temp_dir, "invalid.jpg")
        img.save(img_path)
        
        # Create TXT with invalid normalized values (>1)
        txt_path = os.path.join(temp_dir, "invalid.txt")
        with open(txt_path, 'w') as f:
            f.write("0 1.5 0.5 0.1 0.1\n")  # xc > 1 is invalid
            f.write("0 0.5 0.5 0.1 0.1\n")  # valid
        
        output_path = os.path.join(temp_dir, "_annotations.coco.json")
        
        result = convert_txt_to_coco(
            images_folder=temp_dir,
            txt_folder=temp_dir,
            output_path=output_path,
            class_names=["person"]
        )
        
        # Should skip invalid bbox, keep valid one
        with open(output_path, 'r') as f:
            coco_data = json.load(f)
        
        # Only the valid annotation should remain
        assert len(coco_data["annotations"]) == 1, "Should skip invalid bbox and keep valid one"


class TestRoundTripConversion:
    """Test round-trip conversions to ensure data integrity"""
    
    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    def test_json_to_txt_to_coco_roundtrip(self, temp_dir):
        """Test JSON -> TXT -> COCO maintains bbox accuracy"""
        from PIL import Image
        
        # Create test image
        img = Image.new('RGB', (1920, 1080), color='white')
        img_path = os.path.join(temp_dir, "test.jpg")
        img.save(img_path)
        
        # Create original JSON
        original_json = {
            "frameName": "test.jpg",
            "width": 1920,
            "height": 1080,
            "objects": [
                {
                    "className": "person",
                    "contour": {
                        "points": [
                            {"x": 960, "y": 540},  # Center of image
                            {"x": 1060, "y": 640}  # 100x100 box
                        ]
                    }
                }
            ]
        }
        
        json_path = os.path.join(temp_dir, "test.json")
        with open(json_path, 'w') as f:
            json.dump(original_json, f)
        
        # Step 1: JSON -> TXT
        txt_dir = os.path.join(temp_dir, "txt_output")
        convert_json_to_txt(
            json_path,
            output_dir=txt_dir,
            class_map={"person": 0},
            interactive=False
        )
        
        # Step 2: TXT -> COCO
        coco_path = os.path.join(temp_dir, "_annotations.coco.json")
        convert_txt_to_coco(
            images_folder=temp_dir,
            txt_folder=txt_dir,
            output_path=coco_path,
            class_names=["person"]
        )
        
        # Verify final COCO bbox
        with open(coco_path, 'r') as f:
            coco_data = json.load(f)
        
        assert len(coco_data["annotations"]) == 1
        bbox = coco_data["annotations"][0]["bbox"]
        x, y, w, h = bbox
        
        # Original box: x=960, y=540, w=100, h=100
        # After round-trip, should be close to original
        assert abs(w - 100) < 2, f"Width should be ~100, got {w}"
        assert abs(h - 100) < 2, f"Height should be ~100, got {h}"
        
        # Center should be preserved
        center_x = x + w / 2
        center_y = y + h / 2
        assert abs(center_x - 1010) < 2, f"Center X should be ~1010, got {center_x}"
        assert abs(center_y - 590) < 2, f"Center Y should be ~590, got {center_y}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
