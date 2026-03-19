# Contributing to Universal Annotator UI

First off, thank you for considering contributing to the Universal Annotator! This document contains guidelines and instructions for contributing to the application, specifically focusing on the User Interface (UI) and core components.

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/madan639/universal_annotator
   cd universal_annotator
   ```

2. **Set up a virtual environment (Recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Architecture & Component Development

The application is structured to separate concerns between UI, core logic, and utilities. When adding new features, please respect this structure:

### 1. Core (`core/`)
- `app_window.py`: The main window controller that houses the overarching application logic and connects UI components together.
- `canvas_widget.py`: The custom drawing surface overriding `QWidget`. Handles all direct mouse/keyboard interactions for drawing and editing bounding boxes and polygons.
- `class_management.py`: Logic regarding class discovery, reading/writing `classes.txt`, and prompting the user for unknown labels.

### 2. UI Elements (`ui/`)
- `components/`: Reusable UI widgets (e.g., `labels_panel.py` for the right-hand annotation list).
- `dialogs/`: Modal dialogs (e.g., `help_about_dialog.py` for the Help menu, class creation dialogs).
- `menus.py`: Configuration and layout of the top menu bar.

### 3. Utilities (`utils/`)
- `converters/`: Modules for parsing and exporting different annotation formats (TXT, JSON, COCO).
- `config.py`: Shared constants, UI colors, and default application settings.

## Code Style Guidelines

- **PEP 8**: Follow standard Python conventions (PEP 8) for readability.
- **Type Hints**: Use type hinting for function arguments and return types where possible to make the codebase easier to understand.
- **Docstrings**: Add docstrings to all new classes, primary methods, and complex functions.
- **Logging**: Use the standard Python `logging` module rather than `print()` statements. We rely heavily on logging for debugging mode switches and file IO operations.

## UI Specific Guidelines

When modifying the PyQt5 user interface:
- **Prioritize the Canvas**: Ensure that popups and side panels do not unnecessarily take focus away from `canvas_widget.py` when the user is trying to draw.
- **Status Bar**: Use `self.app_status_bar.set_status()` to provide immediate feedback to users when actions succeed or fail.
- **Shortcuts**: Standardize keyboard shortcuts by registering them via `QShortcut` in `core/app_window.py` or within the localized widget, making sure they do not conflict with 'E' (Edit), 'M' (Draw), 'X' (View), or navigation keys (A/D).

## Testing Procedures

Before submitting a Pull Request, please ensure you have tested the application locally:
1. Ensure the application launches successfully.
2. Test loading an image directory with standard YOLO Format TXT annotations.
3. Verify that your UI changes do not break the core rendering loop in `paintEvent`.
4. Run the test suite (if applicable/present in the `tests/` directory) using `pytest`.

## Pull Request Guidelines

1. **Fork the repository** and create your branch from `main`.
2. Ensure your code follows the style guidelines defined above.
3. **Draft a clear description**: Explain *what* you changed and *why* you changed it inside the PR description.
4. If your PR introduces a new UI element, please include a **screenshot** or **GIF** demonstrating the change.
5. Submit the PR!

Welcome to the community, and happy building!
