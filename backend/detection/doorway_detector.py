"""
Doorway Detection for Blueprint Analysis
Detects doors and openings to understand room connectivity
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class DoorwayDetector:
    """
    Detects doorways in blueprint images

    Strategy:
    1. Detect wall gaps (breaks in wall continuity)
    2. Detect door swing arcs (curved lines)
    3. Filter by size and position
    4. Map to adjacent rooms for connectivity
    """

    def __init__(self, config: Dict = None):
        self.config = config or {
            'min_door_width': 20,      # pixels (scaled)
            'max_door_width': 60,      # pixels (scaled)
            'min_arc_radius': 25,      # pixels (increased from 10)
            'max_arc_radius': 50,      # pixels (decreased from 60)
            'gap_detection_kernel': 3, # morphology kernel size
            'min_gap_confidence': 0.6,  # threshold for gap detection (increased)
            'require_room_proximity': True,  # Only keep doorways near rooms
            'max_doorways_per_room': 6  # Sanity check
        }

    def detect_doorways(
        self,
        binary_image: np.ndarray,
        rooms: List[Dict] = None
    ) -> List[Dict]:
        """
        Detect doorways in a binary blueprint image

        Args:
            binary_image: Binary image (walls are black, spaces are white)
            rooms: Optional list of detected rooms for connectivity mapping

        Returns:
            List of doorway dictionaries with location and properties
        """
        logger.info("Starting doorway detection")

        doorways = []

        # Method 1: Detect door swing arcs (most reliable)
        arc_doorways = self._detect_door_arcs(binary_image)
        logger.info(f"Found {len(arc_doorways)} arc-based doorways")
        doorways.extend(arc_doorways)

        # Method 2: Detect wall gaps
        gap_doorways = self._detect_wall_gaps(binary_image)
        logger.info(f"Found {len(gap_doorways)} gap-based doorways")
        doorways.extend(gap_doorways)

        # Remove duplicates (same doorway detected by multiple methods)
        doorways = self._remove_duplicate_doorways(doorways)
        logger.info(f"After deduplication: {len(doorways)} doorways")

        # If rooms provided, map doorways to room connectivity
        if rooms:
            doorways = self._map_doorways_to_rooms(doorways, rooms)

            # Filter out doorways not near any room (if configured)
            if self.config.get('require_room_proximity', True):
                before_count = len(doorways)
                doorways = [d for d in doorways if d.get('connects_rooms')]
                logger.info(f"Filtered {before_count - len(doorways)} doorways not near rooms")

        # Sanity check: if we have way too many doorways, only keep highest confidence
        max_doorways = len(rooms) * self.config.get('max_doorways_per_room', 6) if rooms else 50
        if len(doorways) > max_doorways:
            logger.warning(f"Too many doorways ({len(doorways)}), keeping top {max_doorways} by confidence")
            doorways.sort(key=lambda d: d['confidence'], reverse=True)
            doorways = doorways[:max_doorways]

        # Add IDs
        for idx, door in enumerate(doorways):
            door['id'] = f'door_{idx:03d}'

        logger.info(f"Doorway detection complete: {len(doorways)} doorways")
        return doorways

    def _detect_door_arcs(self, binary_image: np.ndarray) -> List[Dict]:
        """
        Detect door swing arcs using Hough Circle Transform

        Door arcs appear as quarter-circles in blueprints showing door swing path
        """
        # Invert image (arcs are typically drawn as black lines on white)
        # We want to detect the arc lines themselves
        inverted = cv2.bitwise_not(binary_image)

        # Use Canny edge detection to find arc edges
        edges = cv2.Canny(inverted, 50, 150, apertureSize=3)

        # Detect circles (arcs will appear as partial circles)
        circles = cv2.HoughCircles(
            edges,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=30,  # Minimum distance between circle centers
            param1=50,   # Canny edge threshold
            param2=15,   # Accumulator threshold (lower = more permissive)
            minRadius=self.config['min_arc_radius'],
            maxRadius=self.config['max_arc_radius']
        )

        doorways = []

        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")

            for (x, y, r) in circles:
                # Verify this is a door arc (not a full circle)
                # Check if it's a partial arc by examining pixel density
                is_partial = self._verify_partial_arc(inverted, x, y, r)

                if is_partial:
                    doorways.append({
                        'center': [int(x), int(y)],
                        'radius': int(r),
                        'type': 'arc',
                        'confidence': 0.8,  # High confidence for arc detection
                        'bounding_box': [x - r, y - r, x + r, y + r]
                    })

        return doorways

    def _verify_partial_arc(
        self,
        edge_image: np.ndarray,
        cx: int,
        cy: int,
        radius: int
    ) -> bool:
        """
        Verify if detected circle is actually a partial arc (door swing)

        Full circles (like tables) should be rejected
        Partial arcs (90-120 degrees) should be accepted
        """
        # Sample points around the circle perimeter
        angles = np.linspace(0, 2 * np.pi, 36)  # Every 10 degrees
        edge_points = 0

        for angle in angles:
            x = int(cx + radius * np.cos(angle))
            y = int(cy + radius * np.sin(angle))

            # Check if point is within image bounds
            if 0 <= y < edge_image.shape[0] and 0 <= x < edge_image.shape[1]:
                if edge_image[y, x] > 0:
                    edge_points += 1

        # Door arcs typically cover 25-35% of circle (90-126 degrees)
        # Full circles would have >70% coverage
        # Be more strict to avoid detecting furniture/fixtures
        coverage = edge_points / len(angles)

        return 0.20 < coverage < 0.45  # Stricter partial arc range

    def _detect_wall_gaps(self, binary_image: np.ndarray) -> List[Dict]:
        """
        Detect gaps in walls that indicate doorways

        Strategy:
        1. Identify wall skeleton
        2. Find discontinuities (gaps)
        3. Filter by gap size to distinguish doors from windows/other gaps
        """
        # Create wall skeleton by inverting and thinning
        inverted = cv2.bitwise_not(binary_image)

        # Apply morphological operations to isolate walls
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (self.config['gap_detection_kernel'], self.config['gap_detection_kernel'])
        )

        # Erode to find gaps
        eroded = cv2.erode(inverted, kernel, iterations=1)

        # Find contours in eroded image
        contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        doorways = []

        for contour in contours:
            area = cv2.contourArea(contour)

            # Skip very small contours (noise)
            if area < 100:
                continue

            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)

            # Check if dimensions match doorway size
            # Doorways are typically narrow (one dimension small, one larger)
            min_dim = min(w, h)
            max_dim = max(w, h)

            if (self.config['min_door_width'] <= min_dim <= self.config['max_door_width'] and
                max_dim > min_dim * 1.5):  # Must be elongated

                # Calculate centroid
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                else:
                    cx, cy = x + w // 2, y + h // 2

                doorways.append({
                    'center': [cx, cy],
                    'width': int(min_dim),
                    'length': int(max_dim),
                    'type': 'gap',
                    'confidence': 0.5,  # Medium confidence for gap detection
                    'bounding_box': [x, y, x + w, y + h]
                })

        return doorways

    def _remove_duplicate_doorways(self, doorways: List[Dict]) -> List[Dict]:
        """
        Remove duplicate doorways detected by multiple methods

        Doorways within 20 pixels of each other are considered duplicates
        Keep the one with higher confidence
        """
        if len(doorways) <= 1:
            return doorways

        # Sort by confidence (highest first)
        doorways.sort(key=lambda d: d['confidence'], reverse=True)

        unique_doorways = []

        for door in doorways:
            is_duplicate = False

            for existing in unique_doorways:
                # Calculate distance between centers
                dist = np.sqrt(
                    (door['center'][0] - existing['center'][0]) ** 2 +
                    (door['center'][1] - existing['center'][1]) ** 2
                )

                if dist < 20:  # Within 20 pixels = duplicate
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_doorways.append(door)

        return unique_doorways

    def _map_doorways_to_rooms(
        self,
        doorways: List[Dict],
        rooms: List[Dict]
    ) -> List[Dict]:
        """
        Map each doorway to adjacent rooms for connectivity graph

        A doorway connects two rooms if it's near their boundary
        """
        for door in doorways:
            cx, cy = door['center']
            adjacent_rooms = []

            # Find rooms whose boundaries are near this doorway
            for room in rooms:
                x1, y1, x2, y2 = room['bounding_box']

                # Expand bounding box slightly to catch doorways at edges
                margin = 10
                expanded_bbox = [x1 - margin, y1 - margin, x2 + margin, y2 + margin]

                # Check if doorway center is near room boundary
                if (expanded_bbox[0] <= cx <= expanded_bbox[2] and
                    expanded_bbox[1] <= cy <= expanded_bbox[3]):

                    # Check if it's actually at boundary (not deep inside room)
                    at_boundary = (
                        abs(cx - x1) < margin or abs(cx - x2) < margin or
                        abs(cy - y1) < margin or abs(cy - y2) < margin
                    )

                    if at_boundary:
                        adjacent_rooms.append(room['id'])

            # A valid doorway should connect 1-2 rooms
            # (1 = entrance, 2 = internal door)
            if len(adjacent_rooms) > 0:
                door['connects_rooms'] = adjacent_rooms
            else:
                door['connects_rooms'] = []
                door['confidence'] *= 0.5  # Lower confidence if not near any room

        return doorways


def detect_doorways(
    binary_image: np.ndarray,
    rooms: List[Dict] = None,
    config: Dict = None
) -> List[Dict]:
    """
    Convenience function to detect doorways

    Args:
        binary_image: Binary blueprint image
        rooms: Optional list of detected rooms
        config: Optional configuration dictionary

    Returns:
        List of detected doorways
    """
    detector = DoorwayDetector(config)
    return detector.detect_doorways(binary_image, rooms)
