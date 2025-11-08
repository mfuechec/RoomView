"""
Improved OpenCV Room Detection
Uses hierarchical contour analysis to identify true rooms vs. furniture/details
Key improvement: Analyzes parent-child relationships to find enclosed spaces (rooms)
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# Improved detection configuration
DETECTION_CONFIG = {
    # Size constraints (in pixels after resize to 2000px)
    'min_room_area_pixels': 5000,      # Increased from 1500 - rooms should be substantial
    'max_room_area_pixels': 500000,    # Ignore if too large (probably whole floor)
    'min_room_dimension': 50,          # Min width/height in pixels

    # Shape constraints
    'min_aspect_ratio': 0.2,           # Reject very thin rectangles
    'max_aspect_ratio': 8.0,           # Allow hallways
    'hallway_aspect_ratio': 4.0,

    # Hierarchy filtering
    'min_area_ratio_to_parent': 0.05,  # Room should be at least 5% of parent
    'max_area_ratio_to_parent': 0.85,  # But not more than 85% (too similar)

    # Contour shape quality
    'min_solidity': 0.6,               # Contour area / convex hull area
    'min_extent': 0.5,                 # Contour area / bounding box area

    # Duplicate removal
    'iou_threshold': 0.5,              # Stricter than before
    'max_rooms': 50
}


def detect_rooms_improved(preprocessed: dict) -> List[Dict]:
    """
    Improved room detection using hierarchical analysis

    Key improvements:
    1. Uses contour hierarchy to identify enclosed spaces (rooms)
    2. Better size and shape filtering based on architectural standards
    3. Eliminates furniture/fixtures by analyzing parent-child relationships

    Args:
        preprocessed: Dictionary from preprocess_pipeline containing 'processed' image

    Returns:
        List of detected rooms with bounding boxes
    """

    image = preprocessed['processed']
    original_shape = preprocessed['original_shape']
    logger.info(f"Starting improved detection on image shape: {image.shape}")

    # STEP 1: Find Contours with Hierarchy (3s)
    logger.info("Step 1: Finding contours with hierarchy")
    contours, hierarchy = cv2.findContours(
        image,
        cv2.RETR_TREE,        # Captures parent-child relationships
        cv2.CHAIN_APPROX_SIMPLE
    )

    logger.info(f"Found {len(contours)} total contours")

    if hierarchy is None or len(contours) == 0:
        logger.warning("No contours found")
        return []

    # STEP 2: Extract Candidate Rooms Using Hierarchy (5s)
    logger.info("Step 2: Extracting rooms using hierarchical analysis")
    candidate_rooms = extract_rooms_from_hierarchy(contours, hierarchy[0])

    logger.info(f"Found {len(candidate_rooms)} candidate rooms from hierarchy")

    # STEP 3: Filter by Size and Shape (3s)
    logger.info("Step 3: Filtering by size and shape constraints")
    valid_rooms = filter_by_room_characteristics(candidate_rooms, contours)

    logger.info(f"After filtering: {len(valid_rooms)} valid rooms")

    # STEP 4: Extract Bounding Boxes (2s)
    logger.info("Step 4: Extracting bounding boxes")
    rooms = []
    for idx, contour_idx in enumerate(valid_rooms):
        contour = contours[contour_idx]
        x, y, w, h = cv2.boundingRect(contour)

        # Calculate quality metrics
        area = cv2.contourArea(contour)
        confidence = calculate_room_confidence(contour, (x, y, w, h))

        # Classify type
        aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 1
        type_hint = 'hallway' if aspect_ratio > DETECTION_CONFIG['hallway_aspect_ratio'] else 'room'

        rooms.append({
            'id': f'room_{idx:03d}',
            'bounding_box': [x, y, x + w, y + h],
            'confidence_score': round(confidence, 2),
            'type_hint': type_hint,
            'area_pixels': int(area)
        })

    logger.info(f"Extracted {len(rooms)} room bounding boxes")

    # STEP 5: Remove Overlapping Rooms (2s)
    logger.info("Step 5: Removing overlapping duplicates")
    rooms = remove_duplicates(rooms, iou_threshold=DETECTION_CONFIG['iou_threshold'])

    logger.info(f"After duplicate removal: {len(rooms)} rooms")

    # STEP 6: Sort by area and limit
    rooms.sort(key=lambda r: r['area_pixels'], reverse=True)

    max_rooms = DETECTION_CONFIG['max_rooms']
    if len(rooms) > max_rooms:
        logger.warning(f"Truncating from {len(rooms)} to {max_rooms} rooms")
        rooms = rooms[:max_rooms]

    logger.info(f"Detection complete: {len(rooms)} rooms detected")

    return rooms


def extract_rooms_from_hierarchy(contours: List, hierarchy: np.ndarray) -> List[int]:
    """
    Extract room candidates using contour hierarchy

    Rooms are typically "holes" (white spaces) enclosed by walls (black lines).
    In hierarchy: [Next, Previous, First_Child, Parent]

    Strategy:
    1. Find contours that have a parent (they're inside something)
    2. Check if they're significantly smaller than parent (room inside wall)
    3. Check if they have reasonable size

    Args:
        contours: All detected contours
        hierarchy: Hierarchy array from cv2.findContours

    Returns:
        List of indices for contours that are likely rooms
    """

    room_candidates = []

    for idx in range(len(contours)):
        # Get hierarchy info: [Next, Previous, First_Child, Parent]
        next_contour = hierarchy[idx][0]
        prev_contour = hierarchy[idx][1]
        first_child = hierarchy[idx][2]
        parent_idx = hierarchy[idx][3]

        # FILTER 1: Must have a parent (enclosed by something)
        if parent_idx == -1:
            continue  # Top-level contour, probably the image border or outer wall

        # Get contour area
        area = cv2.contourArea(contours[idx])

        # FILTER 2: Must have minimum size
        if area < DETECTION_CONFIG['min_room_area_pixels']:
            continue

        # FILTER 3: Must not be too large
        if area > DETECTION_CONFIG['max_room_area_pixels']:
            continue

        # FILTER 4: Check relationship with parent
        parent_area = cv2.contourArea(contours[parent_idx])

        if parent_area > 0:
            area_ratio = area / parent_area

            # Room should be significantly smaller than its enclosing contour
            min_ratio = DETECTION_CONFIG['min_area_ratio_to_parent']
            max_ratio = DETECTION_CONFIG['max_area_ratio_to_parent']

            if min_ratio < area_ratio < max_ratio:
                room_candidates.append(idx)
                logger.debug(f"Room candidate {idx}: area={area}, parent_ratio={area_ratio:.2f}")

    return room_candidates


def filter_by_room_characteristics(candidate_indices: List[int], contours: List) -> List[int]:
    """
    Apply shape and quality filters to eliminate false positives

    Filters out:
    - Very thin rectangles (doors, windows)
    - Irregular shapes (furniture details)
    - Too small objects (fixtures, symbols)

    Args:
        candidate_indices: Indices of candidate rooms
        contours: All contours

    Returns:
        Filtered list of room indices
    """

    valid_rooms = []

    for idx in candidate_indices:
        contour = contours[idx]

        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)

        # FILTER 1: Minimum dimensions
        if w < DETECTION_CONFIG['min_room_dimension'] or h < DETECTION_CONFIG['min_room_dimension']:
            logger.debug(f"Rejected {idx}: too small ({w}x{h})")
            continue

        # FILTER 2: Aspect ratio (reject very thin rectangles)
        aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else float('inf')

        if aspect_ratio < DETECTION_CONFIG['min_aspect_ratio']:
            logger.debug(f"Rejected {idx}: aspect ratio too small ({aspect_ratio:.2f})")
            continue

        if aspect_ratio > DETECTION_CONFIG['max_aspect_ratio']:
            logger.debug(f"Rejected {idx}: aspect ratio too large ({aspect_ratio:.2f})")
            continue

        # FILTER 3: Solidity (contour area / convex hull area)
        # Rooms should be fairly solid shapes, not irregular
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        contour_area = cv2.contourArea(contour)

        solidity = contour_area / hull_area if hull_area > 0 else 0

        if solidity < DETECTION_CONFIG['min_solidity']:
            logger.debug(f"Rejected {idx}: low solidity ({solidity:.2f})")
            continue

        # FILTER 4: Extent (contour area / bounding box area)
        # Rooms should fill most of their bounding box
        bbox_area = w * h
        extent = contour_area / bbox_area if bbox_area > 0 else 0

        if extent < DETECTION_CONFIG['min_extent']:
            logger.debug(f"Rejected {idx}: low extent ({extent:.2f})")
            continue

        valid_rooms.append(idx)
        logger.debug(f"Accepted {idx}: area={contour_area:.0f}, aspect={aspect_ratio:.2f}, solidity={solidity:.2f}")

    return valid_rooms


def calculate_room_confidence(contour, bbox: Tuple[int, int, int, int]) -> float:
    """
    Calculate confidence score based on multiple quality metrics

    Args:
        contour: OpenCV contour
        bbox: Bounding box (x, y, w, h)

    Returns:
        Confidence score (0.0 to 1.0)
    """

    x, y, w, h = bbox

    # Metric 1: Rectangularity (how well does it fit the bounding box)
    contour_area = cv2.contourArea(contour)
    bbox_area = w * h
    rectangularity = contour_area / bbox_area if bbox_area > 0 else 0

    # Metric 2: Solidity (how convex is the shape)
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    solidity = contour_area / hull_area if hull_area > 0 else 0

    # Metric 3: Size appropriateness
    # Assume typical room is around 10,000 pixels at 2000px image width
    typical_room_area = 10000
    size_score = min(contour_area / typical_room_area, 1.0)

    # Metric 4: Shape regularity (perimeter vs area)
    perimeter = cv2.arcLength(contour, True)
    # Compactness: 4π * area / perimeter^2 (circle = 1.0, square ≈ 0.785)
    compactness = 4 * np.pi * contour_area / (perimeter ** 2) if perimeter > 0 else 0

    # Weighted combination
    confidence = (
        0.30 * rectangularity +  # Important: rooms are rectangular
        0.25 * solidity +         # Important: rooms are solid shapes
        0.25 * size_score +       # Important: rooms should be substantial
        0.20 * compactness        # Less important: some rooms are irregular
    )

    return min(confidence, 1.0)


def remove_duplicates(rooms: List[Dict], iou_threshold: float = 0.5) -> List[Dict]:
    """
    Remove overlapping rooms using IoU (Intersection over Union)

    Args:
        rooms: List of room dictionaries
        iou_threshold: IoU threshold above which rooms are considered duplicates

    Returns:
        Filtered list of rooms
    """

    if len(rooms) <= 1:
        return rooms

    # Sort by confidence score (keep higher confidence rooms)
    rooms_sorted = sorted(rooms, key=lambda r: r['confidence_score'], reverse=True)

    keep = []
    skip_indices = set()

    for i, room1 in enumerate(rooms_sorted):
        if i in skip_indices:
            continue

        keep.append(room1)

        # Check against remaining rooms
        for j in range(i + 1, len(rooms_sorted)):
            if j in skip_indices:
                continue

            room2 = rooms_sorted[j]
            iou = calculate_iou(room1['bounding_box'], room2['bounding_box'])

            if iou > iou_threshold:
                skip_indices.add(j)
                logger.debug(f"Removing duplicate: IoU={iou:.2f} between {room1['id']} and {room2['id']}")

    logger.info(f"Removed {len(rooms) - len(keep)} duplicate rooms")
    return keep


def calculate_iou(box1: List[int], box2: List[int]) -> float:
    """
    Calculate Intersection over Union (IoU) between two bounding boxes

    Args:
        box1: [x_min, y_min, x_max, y_max]
        box2: [x_min, y_min, x_max, y_max]

    Returns:
        IoU score (0.0 to 1.0)
    """

    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2

    # Calculate intersection area
    x_inter_min = max(x1_min, x2_min)
    y_inter_min = max(y1_min, y2_min)
    x_inter_max = min(x1_max, x2_max)
    y_inter_max = min(y1_max, y2_max)

    if x_inter_max < x_inter_min or y_inter_max < y_inter_min:
        return 0.0

    intersection = (x_inter_max - x_inter_min) * (y_inter_max - y_inter_min)

    # Calculate union area
    area1 = (x1_max - x1_min) * (y1_max - y1_min)
    area2 = (x2_max - x2_min) * (y2_max - y2_min)
    union = area1 + area2 - intersection

    if union == 0:
        return 0.0

    return intersection / union
