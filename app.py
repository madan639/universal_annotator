import sys
import os

# Add parent directory to Python path
current_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from universal_annotator.app.main import main

if __name__ == "__main__":
    main()
