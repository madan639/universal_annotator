import cv2
import numpy as np
import logging
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont


class CanvasWidget(QWidget):
    """Canvas widget for displaying images and bounding boxes."""
    
    box_clicked_on_canvas = pyqtSignal(int) # Emits the index of the clicked box
    zoom_changed = pyqtSignal(float)  # Signal to emit zoom level
    drawing_cancelled = pyqtSignal() # Signal when drawing is cancelled by Esc
    box_added = pyqtSignal(tuple)  # Signal when new box is added
    
    def __init__(self, parent=None, mode="view", classes=None):
        super().__init__(parent)
        self.mode = mode
        self.classes = classes or []
        self.image = None  # Original image (numpy array)
        self.display_image = None  # Displayed image (for canvas)
        self.boxes = []  # List of boxes: [(x, y, w, h, class_id), ...]
        self.current_box = None  # Box being drawn
        self.start_pos = None
        self.current_class = 0
        self.changed = False
        self.selected_boxes = set()  # Indices of selected boxes to display
        self.scaled_pixmap = None  # Cache scaled pixmap
        self.offset_x = 0
        self.offset_y = 0
        self.zoom_level = 1.0
        self.zoom_factor = 1.1
        self.scale_x = 1.0
        self.scale_y = 1.0
        
        self.is_drawing_enabled = False # New state for M key mode
        # When drawing inside an existing box, store parent box index and bounds
        self.parent_box_index = None
        self.parent_box_bounds = None  # (x, y, w, h)
        # --- Editing State ---
        self.editing_box_index = None
        self.editing_handle = None
        self.hovered_box_index = None
        
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True) # Needed for hover effects and cursor changes

    def set_drawing_mode(self, enabled):
        """Enable or disable the drawing sub-mode."""
        self.is_drawing_enabled = enabled
        logging.info(f"Drawing mode set to: {enabled}")

    def toggle_drawing_mode(self):
        """Toggles the drawing mode on or off."""
        self.is_drawing_enabled = not self.is_drawing_enabled
        return self.is_drawing_enabled

    def load_image(self, image_path):
        """Load an image from file."""
        self.image = cv2.imread(image_path)
        if self.image is None:
            logging.error(f"Cannot load image: {image_path}")
            raise FileNotFoundError(f"Cannot load image: {image_path}")
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.display_image = self.image.copy()
        self.current_box = None
        self.boxes = []
        self.selected_boxes = set()
        self.changed = False
        self.zoom_level = 1.0 # Reset zoom when new image is loaded
        # Emit signal to reset zoom display in status bar
        self.zoom_changed.emit(self.zoom_level)
        self.update()

    def get_handle_at_pos(self, img_x, img_y):
        """Check if a click is on a handle of any selected box."""
        handle_size = 8 / self.scale_x # 8 pixel handle in screen space
        
        # Iterate in reverse so top-most boxes are checked first
        # Filter out None values from selected_boxes before sorting to prevent TypeError
        valid_selected_indices = [i for i in self.selected_boxes if i is not None]

        for idx in sorted(valid_selected_indices, reverse=True):
            if not (0 <= idx < len(self.boxes)): # This check is now safer
                continue
            
            x, y, w, h, _ = self.boxes[idx]
            
            handles = {
                'top-left': (x, y), 'top-right': (x + w, y),
                'bottom-left': (x, y + h), 'bottom-right': (x + w, y + h),
                'top': (x + w / 2, y), 'bottom': (x + w / 2, y + h),
                'left': (x, y + h / 2), 'right': (x + w, y + h / 2),
            }

            for name, (hx, hy) in handles.items():
                if abs(img_x - hx) < handle_size and abs(img_y - hy) < handle_size:
                    return idx, name

            # Check if inside the box for moving
            if x < img_x < x + w and y < img_y < y + h:
                return idx, 'move'
                
        return None, None

    def _update_cursor(self, pos):
        """Update cursor based on hover position."""
        if self.mode != "edit":
            self.setCursor(Qt.ArrowCursor)
            return

        img_x = int((pos.x() - self.offset_x) / self.scale_x)
        img_y = int((pos.y() - self.offset_y) / self.scale_y)

        _, handle = self.get_handle_at_pos(img_x, img_y)

        if handle in ['top-left', 'bottom-right']:
            self.setCursor(Qt.SizeFDiagCursor)
        elif handle in ['top-right', 'bottom-left']:
            self.setCursor(Qt.SizeBDiagCursor)
        elif handle in ['top', 'bottom']:
            self.setCursor(Qt.SizeVerCursor)
        elif handle in ['left', 'right']:
            self.setCursor(Qt.SizeHorCursor)
        elif handle == 'move':
            self.setCursor(Qt.SizeAllCursor)
        else:
            self.setCursor(Qt.CrossCursor if self.mode == "edit" else Qt.ArrowCursor)

    def mousePressEvent(self, event):
        """Handle mouse press for box drawing."""
        logging.info(f"[NESTED_DRAW] ======== MOUSE PRESS ========")
        logging.info(f"[NESTED_DRAW] mode={self.mode}, image_loaded={self.image is not None}, is_drawing_enabled={self.is_drawing_enabled}, num_boxes={len(self.boxes)}")
        
        if self.mode != "edit" or self.image is None:
            logging.info(f"[NESTED_DRAW] ✗ REJECTED: mode={self.mode}, image={self.image is not None}")
            return
        
        pos = event.pos()
        img_x = int((pos.x() - self.offset_x) / self.scale_x)
        img_y = int((pos.y() - self.offset_y) / self.scale_y)
        
        # Clamp to image bounds
        img_x = max(0, min(img_x, self.image.shape[1] - 1))
        img_y = max(0, min(img_y, self.image.shape[0] - 1))

        logging.info(f"[NESTED_DRAW] Click at img_coords=({img_x}, {img_y})")

        # --- Priority 1: Check for editing handles FIRST ---
        # This is the most specific action. If a user clicks a handle, they want to edit.
        box_idx, handle = self.get_handle_at_pos(img_x, img_y)
        if box_idx is not None and handle is not None:
            # If drawing mode is on, we don't want to start an edit.
            if not self.is_drawing_enabled:
                logging.info(f"[EDITING] Starting edit on box {box_idx} with handle '{handle}'")
                self.editing_box_index = box_idx
                self.editing_handle = handle
                self.start_pos = (img_x, img_y)
                self.original_box_on_edit = self.boxes[box_idx]
                return # Action handled, stop here.

        # --- Priority 2: Check for nested drawing or selection ---
        candidate_boxes = [(w * h, idx, (x, y, w, h)) for idx, (x, y, w, h, _) in enumerate(self.boxes) if x <= img_x < x + w and y <= img_y < y + h]
        logging.info(f"[NESTED_DRAW] Found {len(candidate_boxes)} boxes under cursor for potential selection/drawing.")

        if candidate_boxes:
            # Pick the smallest box under the cursor
            candidate_boxes.sort(key=lambda t: t[0])
            _, best_idx, best_bounds = candidate_boxes[0] # Smallest area is at index 0
            
            logging.info(f"[NESTED_DRAW] Best box: idx={best_idx}, bounds={best_bounds}, is_drawing_enabled={self.is_drawing_enabled}")

            # If drawing mode is enabled, start drawing a new (child) box INSIDE
            # the clicked box without emitting selection—user is in draw mode.
            if self.is_drawing_enabled:
                self.parent_box_index = best_idx
                self.parent_box_bounds = best_bounds
                logging.info(f"[NESTED_DRAW] ✓ STARTING NESTED DRAW - parent_box_index={best_idx}, parent_box_bounds={best_bounds}")
                self.start_pos = (img_x, img_y)
                self.editing_box_index = None
                # Ensure the parent box is visible in this canvas instance
                self.selected_boxes.add(best_idx)
                self.update()
                return

            # Otherwise perform normal selection (not in drawing mode)
            logging.info(f"[NESTED_DRAW] Not in drawing mode - emitting selection for box {best_idx}")
            self.box_clicked_on_canvas.emit(best_idx)
            # A box was clicked for selection, so we don't proceed to drawing.
            return
        
        # --- Priority 3: If no other action was taken, check if we can draw a new box ---
        if not self.is_drawing_enabled:
            # If not in drawing mode, do not start drawing a new box.
            # This prevents accidental boxes when trying to click/drag the canvas.
            return

        # --- If not editing, start drawing a new box ---
        logging.debug(f"Mouse press at widget({pos.x()},{pos.y()}) -> image({img_x},{img_y})")
        self.start_pos = (img_x, img_y)
        self.editing_box_index = None # Ensure we are not in edit mode

    def mouseMoveEvent(self, event):
        """Handle mouse move for box preview or editing."""
        if self.image is None:
            return

        pos = event.pos()
        self._update_cursor(pos) # Update cursor on hover

        if self.mode != "edit" or self.start_pos is None:
            return
        
        img_x = int((pos.x() - self.offset_x) / self.scale_x)
        img_y = int((pos.y() - self.offset_y) / self.scale_y)
        
        # Clamp to image bounds
        img_x = max(0, min(img_x, self.image.shape[1] - 1))
        img_y = max(0, min(img_y, self.image.shape[0] - 1))
        
        # --- Handle box editing ---
        if self.editing_box_index is not None:
            self.changed = True
            orig_x, orig_y, orig_w, orig_h, class_id = self.original_box_on_edit
            dx = img_x - self.start_pos[0]
            dy = img_y - self.start_pos[1]

            x, y, w, h = orig_x, orig_y, orig_w, orig_h

            if self.editing_handle == 'move':
                x, y = orig_x + dx, orig_y + dy
            # Corner handles
            elif 'right' in self.editing_handle: w = orig_w + dx
            elif 'left' in self.editing_handle: x, w = orig_x + dx, orig_w - dx
            
            if 'bottom' in self.editing_handle: h = orig_h + dy
            elif 'top' in self.editing_handle: y, h = orig_y + dy, orig_h - dy

            # Normalize box (w/h must be positive)
            if w < 0: x, w = x + w, -w
            if h < 0: y, h = y + h, -h

            self.boxes[self.editing_box_index] = (x, y, w, h, class_id)
            self.update()
            return

        # --- Handle new box drawing ---
        if self.start_pos:
            x1, y1 = self.start_pos
            x2, y2 = img_x, img_y
            
            logging.info(f"[NESTED_DRAW] mouseMoveEvent: parent_box_bounds={self.parent_box_bounds}, start=({x1},{y1}), current=({x2},{y2})")
            
            # If drawing inside a parent box, clamp the mouse positions to parent bounds
            if self.parent_box_bounds is not None:
                px, py, pw, ph = self.parent_box_bounds
                # Clamp both points within parent
                x2 = max(px, min(x2, px + pw))
                y2 = max(py, min(y2, py + ph))
                x1 = max(px, min(x1, px + pw))
                y1 = max(py, min(y1, py + ph))
                logging.info(f"[NESTED_DRAW] Clamped: x1={x1}, y1={y1}, x2={x2}, y2={y2}")

            box_x = min(x1, x2)
            box_y = min(y1, y2)
            box_w = abs(x2 - x1)
            box_h = abs(y2 - y1)
            
            self.current_box = (box_x, box_y, box_w, box_h)
            logging.info(f"[NESTED_DRAW] current_box set to {self.current_box}")
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release to finalize box."""
        if self.mode != "edit":
            return

        # --- Finalize editing ---
        if self.editing_box_index is not None:
            logging.debug(f"Finished editing box {self.editing_box_index}")
            self.editing_box_index = None
            self.editing_handle = None
            self.start_pos = None
            self.original_box_on_edit = None
            self.update() # Redraw to remove handles if mouse moves away
            return

        # --- Finalize new box ---
        if self.current_box is None:
            return

        x, y, w, h = self.current_box
        if w > 5 and h > 5:  # Minimum box size
            box = (x, y, w, h, self.current_class)
            self.boxes.append(box)
            self.changed = True
            self.box_added.emit(box)
        
        # Reset any parent constraints when a child box is finished
        self.current_box = None
        self.start_pos = None
        self.parent_box_index = None
        self.parent_box_bounds = None
        self.update()

    def keyPressEvent(self, event):
        """Handle key presses, specifically Esc to cancel drawing."""
        if event.key() == Qt.Key_Escape:
            # If a box is actively being drawn, cancel it and consume the event.
            if self.start_pos is not None and self.current_box is not None:
                logging.debug("Drawing cancelled by user via Escape key.")
                self.current_box = None
                self.start_pos = None
                self.drawing_cancelled.emit()
                self.update()
                return  # Event handled, do not propagate.
        
        # For all other keys, or for Esc when not drawing, propagate to parent.
        super().keyPressEvent(event)

    def paintEvent(self, event):
        """Paint the canvas with image and boxes."""
        if self.image is None:
            return
        
        # Convert image to QImage
        h, w, ch = self.image.shape
        bytes_per_line = 3 * w
        qt_image = QImage(self.image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Calculate base scale to fit widget while maintaining aspect ratio
        pixmap = QPixmap.fromImage(qt_image)
        
        # Determine the base scale factor to fit the image within the widget
        widget_aspect_ratio = self.width() / self.height()
        image_aspect_ratio = w / h
        
        if image_aspect_ratio > widget_aspect_ratio:
            base_scale = self.width() / w
        else:
            base_scale = self.height() / h
            
        # Apply zoom level to the base scale
        current_scale = base_scale * self.zoom_level
        
        # Scale the pixmap
        self.scaled_pixmap = pixmap.scaled(int(w * current_scale), int(h * current_scale), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Calculate offset to center the scaled image
        self.offset_x = (self.width() - self.scaled_pixmap.width()) // 2
        self.offset_y = (self.height() - self.scaled_pixmap.height()) // 2
        
        # These scales are for converting widget coordinates back to original image coordinates
        # Calculate scale factors
        self.scale_x = self.scaled_pixmap.width() / w
        self.scale_y = self.scaled_pixmap.height() / h
        
        # Paint on canvas
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black)  # Fill background
        painter.drawPixmap(self.offset_x, self.offset_y, self.scaled_pixmap)
        
        # Color palette for classes (cycles if more classes than colors)
        palette = ["#00ff00", "#ff4444", "#ff9800", "#00bfff", "#ffd700", "#8a2be2", "#ff69b4"]

        # Draw ONLY selected boxes (hide unselected ones completely)
        for idx, box in enumerate(self.boxes):
            x, y, bw, bh, class_id = box

            # Only draw if selected
            if idx not in self.selected_boxes:
                continue

            # Pick color by class id from palette
            color_hex = palette[class_id % len(palette)] if class_id is not None else palette[0]
            
            # Colored outline matching the fill
            color = QColor(color_hex)
            pen = QPen(color)
            pen.setWidth(1)
            painter.setPen(pen)
            
            # Semi-transparent fill with class color
            fill_color = QColor(color_hex)
            fill_color.setAlpha(80)  # Semi-transparent
            painter.setBrush(fill_color)

            # Convert image coords to widget coords
            rx = int(x * self.scale_x) + self.offset_x
            ry = int(y * self.scale_y) + self.offset_y
            rw = int(bw * self.scale_x)
            rh = int(bh * self.scale_y)
            painter.drawRect(rx, ry, rw, rh)

            # Draw handles if in edit mode
            if self.mode == 'edit':
                # Use a white pen with a black outline for high visibility
                handle_pen = QPen(QColor(0, 0, 0, 100)) # More transparent black outline
                handle_pen.setWidth(1)
                painter.setPen(handle_pen)
                painter.setBrush(QColor(255, 255, 255, 80)) # More transparent white fill
                handle_size = 8

                # Draw all 8 handles (corners and mid-points)
                painter.drawRect(rx - handle_size//2, ry - handle_size//2, handle_size, handle_size)  # Top-left
                painter.drawRect(rx + rw - handle_size//2, ry - handle_size//2, handle_size, handle_size)  # Top-right
                painter.drawRect(rx - handle_size//2, ry + rh - handle_size//2, handle_size, handle_size)  # Bottom-left
                painter.drawRect(rx + rw - handle_size//2, ry + rh - handle_size//2, handle_size, handle_size)  # Bottom-right
                painter.drawRect(rx + rw//2 - handle_size//2, ry - handle_size//2, handle_size, handle_size)  # Top
                painter.drawRect(rx + rw//2 - handle_size//2, ry + rh - handle_size//2, handle_size, handle_size)  # Bottom
                painter.drawRect(rx - handle_size//2, ry + rh//2 - handle_size//2, handle_size, handle_size)  # Left
                painter.drawRect(rx + rw - handle_size//2, ry + rh//2 - handle_size//2, handle_size, handle_size)  # Right

            # Draw label for selected box
            if self.classes and class_id < len(self.classes):
                class_name = self.classes[class_id]
            else:
                class_name = f"Class {class_id}"
            # Draw label with a small opaque background so it's readable
            font = QFont()
            font.setPointSize(8)
            painter.setFont(font)

            # Measure text size
            fm = painter.fontMetrics()
            text_w = fm.horizontalAdvance(class_name) + 6
            text_h = fm.height() + 2

            # Prefer placing label inside the box at top-left; if there's
            # not enough room (near image top), place inside the box at y+12
            label_x = rx + 5
            label_y = ry - text_h - 2
            # If label would be above the widget (negative), place it inside box
            if label_y < 0:
                label_y = ry + 5

            # Ensure label_x/y are within widget bounds (avoid clipping off-screen)
            label_x = max(2, min(label_x, self.width() - text_w - 2))
            label_y = max(2, min(label_y, self.height() - text_h - 2))

            # Draw background rectangle (semi-opaque black)
            bg_brush = QColor(0, 0, 0, 180)
            painter.setBrush(bg_brush)
            painter.setPen(Qt.NoPen)
            painter.drawRect(label_x - 3, label_y - 1, text_w, text_h)

            # Draw text in white for contrast
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(label_x, label_y + fm.ascent() + 0, class_name)
        
        # Draw preview box while drawing (use green preview)
        if self.current_box is not None and self.mode == "edit":
            x, y, w, h = self.current_box
            pen = QPen(QColor(0, 255, 0))
            pen.setWidth(2)
            painter.setPen(pen)

            # Convert image coords to widget coords
            rx = int(x * self.scale_x) + self.offset_x
            ry = int(y * self.scale_y) + self.offset_y
            rw = int(w * self.scale_x)
            rh = int(h * self.scale_y)
            painter.drawRect(rx, ry, rw, rh)

    def delete_last_box(self):
        """Delete the last box."""
        if self.boxes:
            self.boxes.pop()
            self.changed = True
            self.update()

    def set_class(self, class_id):
        """Set the current class for drawing."""
        self.current_class = class_id

    def clear_boxes(self):
        """Clear all boxes."""
        self.boxes = []
        self.selected_boxes = set()
        self.changed = True
        self.zoom_level = 1.0 # Reset zoom when clearing boxes
        self.update()

    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        if self.image is None:
            return

        # Zoom in/out
        if event.angleDelta().y() > 0:
            self.zoom_level *= self.zoom_factor
        else:
            self.zoom_level /= self.zoom_factor
        
        # Clamp zoom level
        self.zoom_level = max(0.1, min(self.zoom_level, 10.0)) # Min 10%, Max 1000%
        
        logging.debug(f"Zoom level: {self.zoom_level:.2f}")
        self.zoom_changed.emit(self.zoom_level)
        self.update()