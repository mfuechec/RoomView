"""
Text Detection and Filtering
Removes text annotations from blueprints before room detection
"""

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


def detect_and_remove_text(binary_image: np.ndarray) -> np.ndarray:
    """
    Detect and remove text regions from binary blueprint image

    Strategy:
    1. Detect connected components
    2. Filter by text-like characteristics:
       - Small area (text is smaller than rooms)
       - High aspect ratio (text is elongated)
       - Irregular shape (text has curves, not rectangles)
    3. Remove these components

    Args:
        binary_image: Binary image (0=black/lines, 255=white/background)

    Returns:
        Binary image with text regions removed
    """

    # Find all connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        binary_image,
        connectivity=8
    )

    # Create output image (start with original)
    filtered = binary_image.copy()

    text_regions_removed = 0

    for i in range(1, num_labels):  # Skip background (label 0)
        area = stats[i, cv2.CC_STAT_AREA]
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]

        # Skip if already removed
        if w == 0 or h == 0:
            continue

        aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 999

        # TEXT CHARACTERISTIC 1: Small area
        # Text is typically 100-5000 pixels, rooms are > 2000
        if area < 100 or area > 3000:
            continue

        # TEXT CHARACTERISTIC 2: High aspect ratio
        # Text labels are very elongated (e.g., "AUTOVAJA" is ~8:1 or more)
        # Walls forming rooms are more square (1:1 to 4:1)
        if aspect_ratio < 3:  # Too square to be text
            continue

        # TEXT CHARACTERISTIC 3: Irregular shape (low solidity)
        # Text has gaps between letters, walls are solid
        component_mask = (labels == i).astype(np.uint8) * 255
        contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            contour = contours[0]
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            contour_area = cv2.contourArea(contour)

            solidity = contour_area / hull_area if hull_area > 0 else 1

            # Text typically has low solidity (< 0.5) due to letter gaps
            # Walls have high solidity (> 0.7)
            if solidity > 0.6:
                continue

        # This component looks like text - remove it
        filtered[labels == i] = 255  # Set to white (background)
        text_regions_removed += 1

        logger.debug(f"Removed text region: area={area}, aspect={aspect_ratio:.1f}, solidity={solidity:.2f}")

    if text_regions_removed > 0:
        logger.info(f"Removed {text_regions_removed} text-like regions")

    return filtered


def remove_text_using_stroke_analysis(binary_image: np.ndarray) -> np.ndarray:
    """
    Alternative approach: Remove text by analyzing stroke characteristics

    Walls: Long, straight, continuous lines
    Text: Short, curvy, disconnected strokes

    Args:
        binary_image: Binary image

    Returns:
        Image with curvy text strokes removed
    """

    # Find contours
    contours, _ = cv2.findContours(binary_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    filtered = binary_image.copy()
    removed = 0

    for contour in contours:
        area = cv2.contourArea(contour)

        # Skip tiny or huge contours
        if area < 50 or area > 5000:
            continue

        # Calculate contour straightness
        # Straight line: arc_length ≈ distance between endpoints
        # Curvy text: arc_length >> distance between endpoints
        arc_length = cv2.arcLength(contour, closed=False)

        if len(contour) >= 2:
            start = contour[0][0]
            end = contour[-1][0]
            endpoint_dist = np.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)

            # Straightness ratio
            # Straight wall: ~1.0
            # Curvy text: > 2.0
            straightness = arc_length / endpoint_dist if endpoint_dist > 0 else 999

            # Remove very curvy strokes (text)
            if straightness > 2.5:
                cv2.drawContours(filtered, [contour], -1, 255, -1)  # Fill with white
                removed += 1

    if removed > 0:
        logger.info(f"Removed {removed} curvy text strokes")

    return filtered


def filter_text_regions(binary_image: np.ndarray, aggressive: bool = False) -> np.ndarray:
    """
    Main text filtering function - combines multiple strategies

    Args:
        binary_image: Binary image to filter
        aggressive: If True, use more aggressive text removal (may remove small rooms)

    Returns:
        Filtered binary image with text removed
    """

    logger.info("Filtering text regions from blueprint...")

    # Strategy 1: Component-based text detection (safer)
    filtered = detect_and_remove_text(binary_image)

    # Strategy 2: Stroke analysis (optional, more aggressive)
    if aggressive:
        filtered = remove_text_using_stroke_analysis(filtered)

    return filtered
