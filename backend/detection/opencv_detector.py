"""
OpenCV Room Detection
Uses contour detection to identify room boundaries in blueprints
"""

import cv2
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# Detection configuration
DETECTION_CONFIG = {
    'canny_low_threshold': 50,
    'canny_high_threshold': 150,
    'min_room_area_pixels': 1500,
    'max_rooms': 50,
    'iou_threshold': 0.7,
    'hallway_aspect_ratio': 4.0
}


def detect_rooms_opencv(preprocessed: dict) -> List[Dict]:
    """
    Detect room boundaries using OpenCV contour detection
    Estimated time: 15-20 seconds

    Args:
        preprocessed: Dictionary from preprocess_pipeline containing 'processed' image

    Returns:
        List of detected rooms with bounding boxes

    Raises:
        Exception: If detection fails
    """

    image = preprocessed['processed']
    logger.info(f"Starting detection on image shape: {image.shape}")

    # STEP 1: Edge Detection (2s)
    logger.info("Step 1: Edge detection")
    edges = cv2.Canny(
        image,
        threshold1=DETECTION_CONFIG['canny_low_threshold'],
        threshold2=DETECTION_CONFIG['canny_high_threshold'],
        apertureSize=3
    )

    # STEP 2: Find Contours (3s)
    logger.info("Step 2: Finding contours")
    contours, hierarchy = cv2.findContours(
        edges,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE
    )

    logger.info(f"Found {len(contours)} total contours")

    # STEP 3: Filter by Size (2s)
    logger.info("Step 3: Filtering by size")
    min_area = DETECTION_CONFIG['min_room_area_pixels']
    valid_contours = [
        c for c in contours
        if cv2.contourArea(c) > min_area
    ]

    logger.info(f"Filtered to {len(valid_contours)} valid contours (min area: {min_area})")

    # STEP 4: Get Bounding Boxes (5s)
    logger.info("Step 4: Extracting bounding boxes")
    rooms = []
    for idx, contour in enumerate(valid_contours):
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)

        # Calculate confidence based on shape regularity
        area = cv2.contourArea(contour)
        bbox_area = w * h
        confidence = area / bbox_area if bbox_area > 0 else 0

        # Classify as room or hallway based on aspect ratio
        aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 1
        type_hint = 'hallway' if aspect_ratio > DETECTION_CONFIG['hallway_aspect_ratio'] else 'room'

        rooms.append({
            'id': f'room_{idx:03d}',
            'bounding_box': [x, y, x + w, y + h],  # [x_min, y_min, x_max, y_max]
            'confidence_score': round(confidence, 2),
            'type_hint': type_hint,
            'area_pixels': int(area)
        })

    logger.info(f"Extracted {len(rooms)} room bounding boxes")

    # STEP 5: Remove Duplicate/Overlapping Rooms (3s)
    logger.info("Step 5: Removing duplicates")
    rooms = remove_duplicates(rooms, iou_threshold=DETECTION_CONFIG['iou_threshold'])

    logger.info(f"After duplicate removal: {len(rooms)} rooms")

    # STEP 6: Sort by area (largest first)
    rooms.sort(key=lambda r: r['area_pixels'], reverse=True)

    # Limit to max rooms
    max_rooms = DETECTION_CONFIG['max_rooms']
    if len(rooms) > max_rooms:
        logger.warning(f"Truncating from {len(rooms)} to {max_rooms} rooms")
        rooms = rooms[:max_rooms]

    logger.info(f"Detection complete: {len(rooms)} rooms detected")

    return rooms


def remove_duplicates(rooms: List[Dict], iou_threshold: float = 0.7) -> List[Dict]:
    """
    Remove duplicate/overlapping rooms using IoU (Intersection over Union)

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
