"""
Blueprint Analyzer - Adaptive Parameter Selection

Analyzes blueprint characteristics to automatically tune detection parameters.
This solves the "one blueprint works, another fails" problem.
"""

import cv2
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


def analyze_blueprint_characteristics(image: np.ndarray) -> Dict:
    """
    Analyze blueprint image to determine optimal detection parameters

    Detects:
    - Wall thickness (thin vs thick walls)
    - Line density (detailed vs simple)
    - Contrast level (dark vs light)
    - Drawing style (CAD vs hand-drawn vs scanned)

    Args:
        image: Grayscale image

    Returns:
        Dictionary with blueprint characteristics and recommended parameters
    """

    logger.info("Analyzing blueprint characteristics...")

    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Characteristic 1: Wall Thickness
    wall_thickness = estimate_wall_thickness(gray)

    # Characteristic 2: Line Density (how detailed is the blueprint)
    line_density = estimate_line_density(gray)

    # Characteristic 3: Contrast Level
    contrast_level = estimate_contrast(gray)

    # Characteristic 4: Noise Level
    noise_level = estimate_noise(gray)

    # Determine blueprint style
    style = classify_blueprint_style(wall_thickness, line_density, contrast_level, noise_level)

    # Get recommended parameters based on analysis
    params = get_adaptive_parameters(style, wall_thickness, line_density, contrast_level)

    logger.info(f"Blueprint Analysis Results:")
    logger.info(f"  Style: {style}")
    logger.info(f"  Wall Thickness: {wall_thickness:.1f}px")
    logger.info(f"  Line Density: {line_density:.2f}")
    logger.info(f"  Contrast: {contrast_level:.2f}")
    logger.info(f"  Recommended morph_open_size: {params['morph_open_size']}")
    logger.info(f"  Recommended min_room_area: {params['min_room_area_pixels']}")

    return {
        'style': style,
        'wall_thickness': wall_thickness,
        'line_density': line_density,
        'contrast_level': contrast_level,
        'noise_level': noise_level,
        'recommended_params': params
    }


def estimate_wall_thickness(gray: np.ndarray) -> float:
    """
    Estimate average wall thickness in pixels

    Method: Find edges, measure distance between parallel edges
    """

    # Edge detection
    edges = cv2.Canny(gray, 50, 150)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return 5.0  # Default fallback

    # Measure thickness using morphological operations
    # Dilate edges and count iterations needed to connect most edges
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    thicknesses = []
    for i in range(1, 15):
        dilated = cv2.dilate(edges, kernel, iterations=i)
        filled_ratio = np.sum(dilated > 0) / dilated.size

        # When ~5-10% of image is filled, that's roughly wall thickness
        if 0.05 < filled_ratio < 0.15:
            thicknesses.append(i * 3)  # 3px per iteration

    if thicknesses:
        avg_thickness = np.mean(thicknesses)
    else:
        # Fallback: measure median contour width
        widths = []
        for cnt in contours[:50]:  # Sample first 50
            x, y, w, h = cv2.boundingRect(cnt)
            widths.append(min(w, h))
        avg_thickness = np.median(widths) if widths else 5.0

    return float(avg_thickness)


def estimate_line_density(gray: np.ndarray) -> float:
    """
    Estimate how detailed/dense the blueprint lines are

    Higher density = more details, furniture, annotations
    Lower density = clean, simple walls only
    """

    # Edge detection
    edges = cv2.Canny(gray, 50, 150)

    # Calculate percentage of pixels that are edges
    edge_density = np.sum(edges > 0) / edges.size

    return float(edge_density)


def estimate_contrast(gray: np.ndarray) -> float:
    """
    Estimate contrast level (difference between walls and background)
    """

    # Calculate standard deviation of pixel values
    # High std = high contrast, low std = low contrast
    contrast = np.std(gray) / 128.0  # Normalize to 0-2 range

    return float(contrast)


def estimate_noise(gray: np.ndarray) -> float:
    """
    Estimate noise level (useful for scanned blueprints)
    """

    # Use Laplacian variance to detect noise
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    noise = np.var(laplacian)

    # Normalize
    noise_normalized = min(noise / 1000.0, 1.0)

    return float(noise_normalized)


def classify_blueprint_style(wall_thickness: float, line_density: float,
                             contrast: float, noise: float) -> str:
    """
    Classify blueprint into one of several style categories
    """

    # Thick walls, low density = Clean CAD
    if wall_thickness > 8 and line_density < 0.05:
        return 'clean_cad'

    # Thick walls, high density = Detailed CAD with furniture
    if wall_thickness > 8 and line_density >= 0.05:
        return 'detailed_cad'

    # Thin walls, low density = Simple line drawing
    if wall_thickness <= 8 and line_density < 0.05:
        return 'simple_line_drawing'

    # Thin walls, high density = Detailed line drawing
    if wall_thickness <= 8 and line_density >= 0.05:
        return 'detailed_line_drawing'

    # High noise = Scanned
    if noise > 0.3:
        return 'scanned'

    # Default
    return 'mixed_style'


def get_adaptive_parameters(style: str, wall_thickness: float,
                            line_density: float, contrast: float) -> Dict:
    """
    Get recommended detection parameters based on blueprint analysis

    Key insight: Different blueprint styles need different parameters
    """

    # Base parameters (conservative defaults)
    params = {
        'morph_open_size': 5,
        'min_room_area_pixels': 5000,
        'min_solidity': 0.6,
        'denoise_strength': 10,
        'morph_close_size': 3,
    }

    # Adjust based on style
    if style == 'clean_cad':
        # Clean blueprints: minimal opening, but fill hollow rooms
        params['morph_open_size'] = 3
        params['min_room_area_pixels'] = 4000
        params['denoise_strength'] = 5
        params['morph_close_size'] = 7  # Aggressive closing to fill thick-walled rooms
        params['fill_hollow_rooms'] = True  # Enable hollow room filling

    elif style == 'detailed_cad':
        # Lots of details: aggressive filtering
        params['morph_open_size'] = 9  # Remove more details
        params['min_room_area_pixels'] = 8000  # Larger min size
        params['denoise_strength'] = 10
        params['fill_hollow_rooms'] = True  # Enable hollow room filling for thick walls

    elif style == 'simple_line_drawing':
        # Thin walls: gentle processing to preserve structure
        params['morph_open_size'] = 2  # Don't erode thin walls
        params['min_room_area_pixels'] = 3000
        params['morph_close_size'] = 5  # More closing to connect thin walls
        params['denoise_strength'] = 5

    elif style == 'detailed_line_drawing':
        # Thin walls + details: balanced approach
        params['morph_open_size'] = 5
        params['min_room_area_pixels'] = 5000
        params['morph_close_size'] = 4

    elif style == 'scanned':
        # Noisy scans: heavy denoising
        params['morph_open_size'] = 6
        params['denoise_strength'] = 15
        params['min_room_area_pixels'] = 6000

    # Fine-tune based on measurements

    # Adjust morph_open based on line density
    if line_density > 0.08:  # Very detailed
        params['morph_open_size'] = min(params['morph_open_size'] + 2, 11)
    elif line_density < 0.03:  # Very simple
        params['morph_open_size'] = max(params['morph_open_size'] - 2, 2)

    # Adjust min_room_area based on wall thickness
    # Thicker walls = can use smaller min_area (walls won't be confused as rooms)
    if wall_thickness > 10:
        params['min_room_area_pixels'] = int(params['min_room_area_pixels'] * 0.8)
    elif wall_thickness < 5:
        params['min_room_area_pixels'] = int(params['min_room_area_pixels'] * 1.2)

    # Adjust solidity based on style
    # Note: Even CAD drawings have irregular room shapes due to doors/windows
    # Lowered significantly because morphology can create hollow contours
    if style in ['clean_cad', 'detailed_cad']:
        params['min_solidity'] = 0.2  # Very permissive - rooms may be hollow outlines
    else:
        params['min_solidity'] = 0.3  # Hand-drawn may be irregular

    return params


def get_scale_context(gray: np.ndarray, detected_rooms: list) -> Dict:
    """
    Analyze room size distribution to identify outliers

    Helps filter out beds/furniture that might be detected as rooms
    """

    if not detected_rooms:
        return {'median_area': 0, 'min_reasonable_area': 0}

    # Get area distribution
    areas = [r['area_pixels'] for r in detected_rooms]

    median_area = np.median(areas)
    std_area = np.std(areas)

    # Rooms should be within 2 std deviations of median
    # Anything much smaller is probably furniture
    min_reasonable_area = max(median_area - 2 * std_area, median_area * 0.3)

    logger.info(f"Scale context: median room area = {median_area:.0f}px², "
                f"min reasonable = {min_reasonable_area:.0f}px²")

    return {
        'median_area': float(median_area),
        'std_area': float(std_area),
        'min_reasonable_area': float(min_reasonable_area),
        'outlier_threshold': float(median_area * 0.25)  # < 25% of median = probably not a room
    }
