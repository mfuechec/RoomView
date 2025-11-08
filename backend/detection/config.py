"""
Centralized Configuration for Room Detection

Tune these parameters based on your blueprint characteristics:
- Increase min_room_area_pixels if getting too many small false positives
- Decrease min_solidity if rooms have irregular shapes
- Adjust morph_open_size to control detail elimination
"""

# Preprocessing Configuration
PREPROCESSING = {
    # Image sizing
    'max_dimension': 2000,           # Max width/height after resize
                                      # Larger = more detail but slower
                                      # Smaller = faster but may miss details

    # Noise reduction
    'denoise_strength': 10,           # 0-20, higher = more smoothing

    # Contrast enhancement
    'contrast_clip_limit': 2.0,       # CLAHE clip limit

    # Morphological operations (KEY FOR REDUCING FALSE POSITIVES)
    'morph_close_size': 3,            # Close wall gaps (3-7 recommended)
    'morph_close_iterations': 1,

    'morph_open_size': 5,             # Remove small details (5-9 recommended)
                                      # INCREASE THIS to eliminate more furniture/fixtures
    'morph_open_iterations': 1,

    'morph_dilate_size': 2,           # Strengthen walls (2-4 recommended)
    'morph_dilate_iterations': 1,

    # File limits
    'min_file_size': 10_000,
    'max_file_size': 10_485_760       # 10MB
}


# Detection Configuration
DETECTION = {
    # Size constraints (in pixels, based on 2000px max dimension)
    'min_room_area_pixels': 5000,     # Minimum room size
                                      # INCREASE to 8000-10000 if getting tiny false positives
                                      # DECREASE to 3000-4000 for small rooms

    'max_room_area_pixels': 500000,   # Maximum room size
                                      # Prevents detecting entire floor as "room"

    'min_room_dimension': 50,         # Min width/height in pixels
                                      # INCREASE to 80-100 to filter narrow spaces

    # Shape constraints
    'min_aspect_ratio': 0.2,          # Reject very thin rectangles (doors/windows)
    'max_aspect_ratio': 8.0,          # Allow long hallways
    'hallway_aspect_ratio': 4.0,      # Classify as hallway if aspect > this

    # Hierarchy filtering (KEY FOR ACCURACY)
    'min_area_ratio_to_parent': 0.05, # Room should be at least 5% of parent contour
                                       # INCREASE to 0.10 if getting small details inside rooms

    'max_area_ratio_to_parent': 0.85, # Room shouldn't be > 85% of parent
                                       # Prevents detecting near-duplicate contours

    # Shape quality (KEY FOR ELIMINATING IRREGULAR SHAPES)
    'min_solidity': 0.6,              # Contour area / convex hull area
                                      # INCREASE to 0.7-0.8 for stricter filtering
                                      # Lower values allow irregular room shapes

    'min_extent': 0.5,                # Contour area / bounding box area
                                      # How well does the room fill its bounding box
                                      # INCREASE to 0.6-0.7 for rectangular rooms only

    # Duplicate removal
    'iou_threshold': 0.5,             # IoU threshold for duplicate detection
                                      # Lower = more aggressive duplicate removal

    'max_rooms': 50                   # Maximum rooms to return
}


# Preset configurations for different blueprint types

PRESETS = {
    'clean_cad': {
        # For clean CAD exports with minimal noise
        'morph_open_size': 3,
        'min_room_area_pixels': 5000,
        'min_solidity': 0.6,
    },

    'detailed_cad': {
        # For CAD with furniture/fixtures (RECOMMENDED FOR YOUR USE CASE)
        'morph_open_size': 7,          # More aggressive detail removal
        'min_room_area_pixels': 8000,  # Larger minimum size
        'min_solidity': 0.7,           # Stricter shape requirements
        'min_area_ratio_to_parent': 0.10,
    },

    'scanned': {
        # For scanned/photographed blueprints with noise
        'denoise_strength': 15,
        'morph_open_size': 5,
        'min_room_area_pixels': 6000,
        'min_solidity': 0.5,           # More lenient for noise
    },

    'hand_drawn': {
        # For hand-drawn sketches
        'morph_open_size': 4,
        'min_room_area_pixels': 4000,
        'min_solidity': 0.4,           # Very lenient
        'min_extent': 0.4,
    }
}


def apply_preset(preset_name: str) -> tuple:
    """
    Apply a preset configuration

    Args:
        preset_name: One of 'clean_cad', 'detailed_cad', 'scanned', 'hand_drawn'

    Returns:
        Tuple of (preprocessing_config, detection_config)
    """

    if preset_name not in PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(PRESETS.keys())}")

    # Start with base configs
    prep_config = PREPROCESSING.copy()
    det_config = DETECTION.copy()

    # Apply preset overrides
    preset = PRESETS[preset_name]

    for key, value in preset.items():
        if key in prep_config:
            prep_config[key] = value
        elif key in det_config:
            det_config[key] = value

    return prep_config, det_config


# Usage example:
# from detection.config import apply_preset, DETECTION, PREPROCESSING
#
# # Use detailed_cad preset (recommended)
# prep_config, det_config = apply_preset('detailed_cad')
#
# # Or manually tune
# det_config = DETECTION.copy()
# det_config['min_room_area_pixels'] = 10000  # Even stricter
