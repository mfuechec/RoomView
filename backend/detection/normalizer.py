"""
Coordinate Normalization
Converts pixel coordinates to percentage-based (0.0-1.0) format
"""

from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


def normalize_coordinates(items: List[Dict], original_shape: Tuple[int, int, ...]) -> List[Dict]:
    """
    Convert pixel coordinates to normalized 0.0-1.0 range

    Works for both rooms and doorways

    Args:
        items: List of room/doorway dictionaries with coordinates in pixels
        original_shape: Original image shape (height, width, ...)

    Returns:
        List of items with normalized coordinates added
    """
    height, width = original_shape[:2]

    logger.info(f"Normalizing coordinates for {len(items)} items (image: {width}x{height})")

    # Convert all numpy types first
    items = [_convert_numpy_types(item) for item in items]

    for item in items:
        # Handle rooms (have bounding_box)
        if 'bounding_box' in item:
            x_min, y_min, x_max, y_max = item['bounding_box']

            # Normalize to 0.0-1.0 range
            item['bounding_box_normalized'] = [
                round(float(x_min) / width, 4),   # x_min
                round(float(y_min) / height, 4),  # y_min
                round(float(x_max) / width, 4),   # x_max
                round(float(y_max) / height, 4)   # y_max
            ]

            # Keep original pixels for debugging
            item['bounding_box_pixels'] = [int(x_min), int(y_min), int(x_max), int(y_max)]

            # Normalize polygon coordinates if present
            if 'polygon' in item:
                item['polygon_normalized'] = [
                    [round(float(x) / width, 4), round(float(y) / height, 4)]
                    for x, y in item['polygon']
                ]
                # Keep original pixels for debugging
                item['polygon_pixels'] = item['polygon']

            # Calculate normalized area for rooms
            if 'area_pixels' not in item or item.get('type') != 'gap':
                norm_w = item['bounding_box_normalized'][2] - item['bounding_box_normalized'][0]
                norm_h = item['bounding_box_normalized'][3] - item['bounding_box_normalized'][1]
                item['area_normalized'] = round(norm_w * norm_h, 6)

        # Handle doorways (have center)
        if 'center' in item:
            cx, cy = item['center']
            item['center_normalized'] = [
                round(float(cx) / width, 4),
                round(float(cy) / height, 4)
            ]
            item['center_pixels'] = [int(cx), int(cy)]

        # Normalize radius if present (arcs)
        if 'radius' in item:
            item['radius_pixels'] = int(item['radius'])
            # Normalize relative to image width
            item['radius_normalized'] = round(float(item['radius']) / width, 4)

    logger.info("Coordinate normalization complete")

    return items


def _convert_numpy_types(obj):
    """
    Recursively convert numpy types to Python native types for JSON serialization
    """
    import numpy as np

    if isinstance(obj, dict):
        return {k: _convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


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
