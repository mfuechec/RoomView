"""
Debug Visualization Module
Saves intermediate processing steps for debugging and analysis
"""

import cv2
import numpy as np
import os
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DebugVisualizer:
    """
    Saves intermediate images during preprocessing and detection

    Usage:
        visualizer = DebugVisualizer(enabled=True, output_dir='debug_output')
        visualizer.save('1_original', gray_image)
        visualizer.save('2_threshold', binary_image)
        visualizer.save_with_contours('5_detected_rooms', image, contours, rooms)
    """

    def __init__(self, enabled: bool = False, output_dir: str = 'debug_output'):
        self.enabled = enabled
        self.output_dir = Path(output_dir)
        self.session_id = None

        if self.enabled:
            # Create output directory if it doesn't exist
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            logger.info(f"Debug visualization enabled. Session: {self.session_id}")

    def save(self, name: str, image: np.ndarray, description: str = None):
        """Save an image to the debug output directory"""
        if not self.enabled:
            return

        try:
            filename = f"{self.session_id}_{name}.png"
            filepath = self.output_dir / filename

            cv2.imwrite(str(filepath), image)
            logger.debug(f"Saved debug image: {filename}")

            if description:
                logger.info(f"Debug: {name} - {description}")

        except Exception as e:
            logger.warning(f"Failed to save debug image {name}: {e}")

    def save_with_contours(self, name: str, image: np.ndarray,
                          contours: list, room_indices: list = None,
                          color=(0, 255, 0), thickness=2):
        """Save image with contours drawn"""
        if not self.enabled:
            return

        try:
            # Convert grayscale to BGR for colored contours
            if len(image.shape) == 2:
                vis_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            else:
                vis_image = image.copy()

            # Draw all contours or specific room contours
            if room_indices is not None:
                for idx in room_indices:
                    cv2.drawContours(vis_image, contours, idx, color, thickness)
            else:
                cv2.drawContours(vis_image, contours, -1, color, thickness)

            self.save(name, vis_image)

        except Exception as e:
            logger.warning(f"Failed to save debug contours {name}: {e}")

    def save_with_bboxes(self, name: str, image: np.ndarray, rooms: list):
        """Save image with bounding boxes and labels"""
        if not self.enabled:
            return

        try:
            # Convert grayscale to BGR for colored boxes
            if len(image.shape) == 2:
                vis_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            else:
                vis_image = image.copy()

            for room in rooms:
                bbox = room['bounding_box']
                x1, y1, x2, y2 = bbox

                # Draw rectangle
                color = (0, 255, 0) if room.get('confidence_score', 0) > 0.7 else (0, 165, 255)
                cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)

                # Add label
                label = f"{room['id']} ({room.get('confidence_score', 0):.2f})"
                cv2.putText(vis_image, label, (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            self.save(name, vis_image, f"Detected {len(rooms)} rooms")

        except Exception as e:
            logger.warning(f"Failed to save debug bboxes {name}: {e}")

    def save_comparison(self, name: str, images: list, labels: list):
        """Save side-by-side comparison of images"""
        if not self.enabled or not images:
            return

        try:
            # Resize all images to same height
            h = max(img.shape[0] for img in images)
            resized = []

            for img in images:
                if len(img.shape) == 2:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

                scale = h / img.shape[0]
                new_w = int(img.shape[1] * scale)
                resized_img = cv2.resize(img, (new_w, h))
                resized.append(resized_img)

            # Concatenate horizontally
            comparison = np.hstack(resized)

            # Add labels
            for i, label in enumerate(labels):
                x_offset = sum(img.shape[1] for img in resized[:i]) + 10
                cv2.putText(comparison, label, (x_offset, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            self.save(name, comparison)

        except Exception as e:
            logger.warning(f"Failed to save comparison {name}: {e}")


# Global instance - can be enabled via environment variable
DEBUG_MODE = os.environ.get('DEBUG_VISUALIZATION', 'false').lower() == 'true'
debug_viz = DebugVisualizer(enabled=DEBUG_MODE)
