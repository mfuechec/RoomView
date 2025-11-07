"""
Coordinate Normalization
Converts pixel coordinates to percentage-based (0.0-1.0) format
"""

from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


def normalize_coordinates(rooms: List[Dict], original_shape: Tuple[int, int, ...]) -> List[Dict]:
    """
    Convert pixel coordinates to normalized 0.0-1.0 range

    Args:
        rooms: List of room dictionaries with 'bounding_box' in pixels
        original_shape: Original image shape (height, width, ...)

    Returns:
        List of rooms with normalized coordinates added
    """
    height, width = original_shape[:2]

    logger.info(f"Normalizing coordinates for {len(rooms)} rooms (image: {width}x{height})")

    for room in rooms:
        x_min, y_min, x_max, y_max = room['bounding_box']

        # Normalize to 0.0-1.0 range
        room['bounding_box_normalized'] = [
            round(x_min / width, 4),   # x_min
            round(y_min / height, 4),  # y_min
            round(x_max / width, 4),   # x_max
            round(y_max / height, 4)   # y_max
        ]

        # Keep original pixels for debugging
        room['bounding_box_pixels'] = [x_min, y_min, x_max, y_max]

        # Calculate normalized area
        norm_w = room['bounding_box_normalized'][2] - room['bounding_box_normalized'][0]
        norm_h = room['bounding_box_normalized'][3] - room['bounding_box_normalized'][1]
        room['area_normalized'] = round(norm_w * norm_h, 6)

    logger.info("Coordinate normalization complete")

    return rooms


def denormalize_coordinates(
    normalized_box: List[float],
    target_width: int,
    target_height: int
) -> Dict[str, int]:
    """
    Convert normalized coordinates back to pixel coordinates

    Useful for rendering on different canvas sizes

    Args:
        normalized_box: [x_min, y_min, x_max, y_max] in 0.0-1.0 range
        target_width: Target canvas width in pixels
        target_height: Target canvas height in pixels

    Returns:
        Dictionary with x, y, width, height in pixels
    """
    x_min_norm, y_min_norm, x_max_norm, y_max_norm = normalized_box

    x = int(x_min_norm * target_width)
    y = int(y_min_norm * target_height)
    width = int((x_max_norm - x_min_norm) * target_width)
    height = int((y_max_norm - y_min_norm) * target_height)

    return {
        'x': x,
        'y': y,
        'width': width,
        'height': height
    }
