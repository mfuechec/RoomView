"""
Adaptive OpenCV Room Detection
Automatically adjusts parameters based on blueprint characteristics
"""

import cv2
import numpy as np
from typing import List, Dict
import logging

from detection.blueprint_analyzer import analyze_blueprint_characteristics, get_scale_context
from detection.opencv_detector_improved import (
    extract_rooms_from_hierarchy,
    filter_by_room_characteristics,
    remove_duplicates,
    calculate_iou,
    DETECTION_CONFIG
)
from detection.debug_visualizer import debug_viz

logger = logging.getLogger(__name__)


def calculate_room_confidence_score(contour, bounding_box, style: str) -> tuple:
    """
    Calculate weighted confidence score for a room candidate

    Returns: (score, metrics_dict)

    Instead of hard thresholds, this uses weighted scoring where
    different metrics matter more/less depending on blueprint style
    """
    x, y, w, h = bounding_box

    # Calculate all metrics
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    contour_area = cv2.contourArea(contour)

    solidity = contour_area / hull_area if hull_area > 0 else 0

    bbox_area = w * h
    extent = contour_area / bbox_area if bbox_area > 0 else 0

    aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else float('inf')

    # Normalize aspect ratio to 0-1 score (1.0 = perfect square, decreases as ratio increases)
    # Good range: 1:1 to 3:1, acceptable up to 8:1
    if aspect_ratio <= 3:
        aspect_score = 1.0
    elif aspect_ratio <= 8:
        aspect_score = 1.0 - ((aspect_ratio - 3) / 5) * 0.5  # Decays to 0.5
    else:
        aspect_score = 0.0  # Too elongated

    # Normalize solidity (already 0-1, but clip low values)
    solidity_score = min(solidity, 1.0)

    # Normalize extent (already 0-1)
    extent_score = min(extent, 1.0)

    # Size score (relative to expected room size)
    # Assume rooms are 5000-100000 pixels, ideal around 20000
    size_score = 1.0 if 5000 < contour_area < 100000 else 0.5

    # VARIABLE WEIGHTING based on blueprint style
    if style in ['clean_cad', 'detailed_cad']:
        # CAD blueprints: solidity/extent unreliable due to hollow outlines
        # Rely more on aspect ratio and size
        weights = {
            'solidity': 0.1,
            'extent': 0.2,
            'aspect_ratio': 0.5,
            'size': 0.2
        }
    elif style in ['simple_line_drawing', 'detailed_line_drawing']:
        # Line drawings: shapes should be clean, solidity matters
        weights = {
            'solidity': 0.3,
            'extent': 0.3,
            'aspect_ratio': 0.3,
            'size': 0.1
        }
    else:  # mixed_style, scanned
        # Balanced weighting
        weights = {
            'solidity': 0.25,
            'extent': 0.25,
            'aspect_ratio': 0.3,
            'size': 0.2
        }

    # Calculate weighted score
    score = (
        weights['solidity'] * solidity_score +
        weights['extent'] * extent_score +
        weights['aspect_ratio'] * aspect_score +
        weights['size'] * size_score
    )

    metrics = {
        'solidity': solidity,
        'extent': extent,
        'aspect_ratio': aspect_ratio,
        'solidity_score': solidity_score,
        'extent_score': extent_score,
        'aspect_score': aspect_score,
        'size_score': size_score,
        'final_score': score
    }

    return score, metrics


def detect_rooms_adaptive(preprocessed: dict) -> List[Dict]:
    """
    Adaptive room detection that tunes parameters based on blueprint analysis

    Key improvement over opencv_detector_improved.py:
    - Analyzes blueprint FIRST to detect style
    - Adjusts parameters automatically
    - Handles thin walls, thick walls, detailed drawings, simple drawings

    Args:
        preprocessed: Dictionary from preprocess_pipeline containing 'processed' image

    Returns:
        List of detected rooms with bounding boxes
    """

    image = preprocessed['processed']
    logger.info(f"Starting ADAPTIVE detection on image shape: {image.shape}")

    # STEP 0: Analyze blueprint characteristics (NEW!)
    logger.info("Step 0: Analyzing blueprint characteristics")
    analysis = analyze_blueprint_characteristics(image)

    # Get adaptive parameters
    adaptive_params = analysis['recommended_params']
    logger.info(f"Using adaptive parameters for style: {analysis['style']}")

    # Override default config with adaptive params
    config = DETECTION_CONFIG.copy()
    config['min_room_area_pixels'] = adaptive_params['min_room_area_pixels']
    config['min_solidity'] = adaptive_params['min_solidity']

    # STEP 1: Find Contours with Hierarchy
    logger.info("Step 1: Finding contours with hierarchy")
    contours, hierarchy = cv2.findContours(
        image,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE
    )

    logger.info(f"Found {len(contours)} total contours")

    if hierarchy is None or len(contours) == 0:
        logger.warning("No contours found")
        return []

    # STEP 2: Extract Candidate Rooms Using Hierarchy
    logger.info("Step 2: Extracting rooms using hierarchical analysis")
    candidate_rooms = extract_rooms_from_hierarchy(contours, hierarchy[0])

    logger.info(f"Found {len(candidate_rooms)} candidate rooms from hierarchy")

    # FALLBACK: If hierarchy found few rooms, supplement with contour-based approach
    if len(candidate_rooms) < 3:
        logger.warning(f"Hierarchy found only {len(candidate_rooms)} rooms - using HYBRID approach")
        size_based_rooms = extract_rooms_by_size(contours, config)
        # Merge and deduplicate
        candidate_rooms = list(set(candidate_rooms + size_based_rooms))
        logger.info(f"After hybrid approach: {len(candidate_rooms)} candidate rooms")

    # STEP 3: Filter by Size and Shape (using SCORE-BASED filtering)
    logger.info("Step 3: Filtering by size and shape using SCORE-BASED approach")
    valid_rooms = filter_by_room_characteristics_adaptive(
        candidate_rooms,
        contours,
        config,
        analysis['style']  # Pass style for variable weighting
    )

    logger.info(f"After filtering: {len(valid_rooms)} valid rooms")

    # STEP 4: Extract Bounding Boxes and Polygons
    logger.info("Step 4: Extracting bounding boxes and polygon shapes")
    rooms = []
    for idx, contour_idx in enumerate(valid_rooms):
        contour = contours[contour_idx]
        x, y, w, h = cv2.boundingRect(contour)

        area = cv2.contourArea(contour)
        confidence, _ = calculate_room_confidence_score(contour, (x, y, w, h), analysis['style'])

        aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 1
        type_hint = 'hallway' if aspect_ratio > config['hallway_aspect_ratio'] else 'room'

        # Simplify contour polygon for more manageable point count
        # Douglas-Peucker algorithm with epsilon = 0.5% of perimeter
        epsilon = 0.005 * cv2.arcLength(contour, True)
        simplified_contour = cv2.approxPolyDP(contour, epsilon, True)

        # Convert to list of [x, y] points
        polygon = simplified_contour.reshape(-1, 2).tolist()

        rooms.append({
            'id': f'room_{idx:03d}',
            'bounding_box': [x, y, x + w, y + h],
            'polygon': polygon,  # NEW: actual room shape
            'confidence_score': round(confidence, 2),
            'type_hint': type_hint,
            'area_pixels': int(area)
        })

    # STEP 5: Scale-based filtering (NEW!)
    logger.info("Step 5: Applying scale-based filtering")
    if len(rooms) > 3:  # Need enough rooms to establish scale context
        scale_context = get_scale_context(image, rooms)

        # Filter out rooms that are too small compared to others
        # (This catches beds/furniture that passed earlier filters)
        rooms_filtered = [
            r for r in rooms
            if r['area_pixels'] >= scale_context['outlier_threshold']
        ]

        if len(rooms_filtered) < len(rooms):
            logger.info(f"Scale filtering removed {len(rooms) - len(rooms_filtered)} outliers")
            rooms = rooms_filtered

    # STEP 6: Remove Overlapping Rooms
    logger.info("Step 6: Removing overlapping duplicates")
    rooms = remove_duplicates(rooms, iou_threshold=config['iou_threshold'])

    logger.info(f"After duplicate removal: {len(rooms)} rooms")

    # STEP 7: Sort and limit
    rooms.sort(key=lambda r: r['area_pixels'], reverse=True)

    max_rooms = config['max_rooms']
    if len(rooms) > max_rooms:
        logger.warning(f"Truncating from {len(rooms)} to {max_rooms} rooms")
        rooms = rooms[:max_rooms]

    logger.info(f"ADAPTIVE detection complete: {len(rooms)} rooms detected")

    # Add metadata about detection
    for room in rooms:
        room['detection_mode'] = 'adaptive'
        room['blueprint_style'] = analysis['style']

    # Debug visualization - save final result
    debug_viz.save_with_bboxes('4_final_detection', image, rooms)

    return rooms


def extract_rooms_by_size(contours: List, config: Dict) -> List[int]:
    """
    Fallback: Extract room candidates based on size alone (no hierarchy)

    Used when blueprints don't have parent-child structure
    Simply filters contours by size range

    Args:
        contours: All detected contours
        config: Detection configuration

    Returns:
        List of indices for contours that match room size criteria
    """

    room_candidates = []
    min_area = config['min_room_area_pixels']
    max_area = config['max_room_area_pixels']

    for idx in range(len(contours)):
        area = cv2.contourArea(contours[idx])

        if min_area < area < max_area:
            room_candidates.append(idx)
            logger.info(f"Size-based candidate {idx}: area={area}")

    logger.info(f"Fallback size-based extraction found {len(room_candidates)} candidates")
    return room_candidates


def filter_by_room_characteristics_adaptive(
    candidate_indices: List[int],
    contours: List,
    config: Dict,
    style: str
) -> List[int]:
    """
    Filter using SCORE-BASED approach with variable weighting

    Instead of hard thresholds, calculates weighted confidence score
    Different metrics weighted differently based on blueprint style
    """

    valid_rooms = []
    # LOWERED from 0.5 to 0.3 based on ground truth analysis
    # Baseline showed severe under-detection (only 36/78 rooms found)
    min_score_threshold = 0.3

    for idx in candidate_indices:
        contour = contours[idx]

        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)

        # HARD FILTER 1: Minimum dimensions (still enforce this)
        min_dim = config.get('min_room_dimension', 50)
        if w < min_dim or h < min_dim:
            logger.info(f"Rejected {idx}: too small ({w}x{h})")
            continue

        # SCORE-BASED FILTERING
        score, metrics = calculate_room_confidence_score(
            contour,
            (x, y, w, h),
            style
        )

        if score < min_score_threshold:
            logger.info(
                f"Rejected {idx}: low score {score:.2f} "
                f"(solidity={metrics['solidity']:.2f}, extent={metrics['extent']:.2f}, "
                f"aspect={metrics['aspect_ratio']:.2f})"
            )
            continue

        valid_rooms.append(idx)
        logger.info(
            f"Accepted {idx}: score={score:.2f} "
            f"(solidity={metrics['solidity']:.2f}, extent={metrics['extent']:.2f}, "
            f"aspect={metrics['aspect_ratio']:.2f}, area={cv2.contourArea(contour):.0f})"
        )

    return valid_rooms
