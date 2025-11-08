"""
Adaptive Image Preprocessing Pipeline
Adjusts preprocessing parameters based on blueprint characteristics
"""

import cv2
import numpy as np
from io import BytesIO
from PIL import Image
import logging

from detection.blueprint_analyzer import analyze_blueprint_characteristics
from detection.debug_visualizer import debug_viz

logger = logging.getLogger(__name__)

# Base configuration
BASE_CONFIG = {
    'max_dimension': 2000,
    'denoise_strength': 10,
    'contrast_clip_limit': 2.0,
    'morph_close_size': 3,
    'morph_close_iterations': 1,
    'morph_open_size': 5,
    'morph_open_iterations': 1,
    'morph_dilate_size': 2,
    'morph_dilate_iterations': 1,
    'min_file_size': 10_000,
    'max_file_size': 10_485_760
}


def preprocess_pipeline_adaptive(image_data: bytes) -> dict:
    """
    Adaptive preprocessing pipeline that adjusts parameters based on blueprint analysis

    Key improvement: Analyzes blueprint FIRST, then applies appropriate processing

    Args:
        image_data: Raw image bytes

    Returns:
        Dictionary containing:
            - processed: Binary image ready for detection
            - original_shape: Original image dimensions
            - scale_factor: Ratio of original to processed size
            - analysis: Blueprint characteristics
    """

    # STAGE 1: Decode & Validate
    logger.info("Stage 1: Decoding image")
    raw_image = decode_image(image_data)

    if raw_image is None:
        raise ValueError("Invalid image data - unable to decode")

    original_shape = raw_image.shape
    logger.info(f"Original image shape: {original_shape}")

    # STAGE 2: Resize
    logger.info("Stage 2: Resizing image")
    resized = resize_maintain_aspect_ratio(
        raw_image,
        max_dimension=BASE_CONFIG['max_dimension']
    )

    # STAGE 3: Convert to Grayscale
    logger.info("Stage 3: Converting to grayscale")
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    debug_viz.save('1_grayscale', gray, "Converted to grayscale")

    # STAGE 3.5: ANALYZE BLUEPRINT (NEW!)
    logger.info("Stage 3.5: Analyzing blueprint for adaptive parameters")
    analysis = analyze_blueprint_characteristics(gray)
    adaptive_params = analysis['recommended_params']

    logger.info(f"Detected style: {analysis['style']}")
    logger.info(f"Using adaptive denoise: {adaptive_params['denoise_strength']}")
    logger.info(f"Using adaptive morph_open: {adaptive_params['morph_open_size']}")

    # STAGE 4: Noise Reduction (ADAPTIVE)
    logger.info("Stage 4: Reducing noise (adaptive strength)")
    denoised = cv2.fastNlMeansDenoising(
        gray,
        h=adaptive_params['denoise_strength'],
        templateWindowSize=7,
        searchWindowSize=21
    )

    # STAGE 5: Contrast Enhancement
    logger.info("Stage 5: Enhancing contrast")
    clahe = cv2.createCLAHE(
        clipLimit=BASE_CONFIG['contrast_clip_limit'],
        tileGridSize=(8, 8)
    )
    enhanced = clahe.apply(denoised)

    # STAGE 6: Thresholding
    logger.info("Stage 6: Applying threshold")
    _, binary = cv2.threshold(
        enhanced,
        0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    debug_viz.save('2_threshold', binary, "After Otsu thresholding")

    # STAGE 7: Adaptive Morphological Operations
    logger.info("Stage 7: Morphological operations (ADAPTIVE)")
    processed = apply_adaptive_morphology(binary, adaptive_params)
    debug_viz.save('3_morphology', processed, "After adaptive morphology")

    scale_factor = original_shape[0] / processed.shape[0]

    logger.info(f"Adaptive preprocessing complete. Output shape: {processed.shape}, Scale factor: {scale_factor:.2f}")

    return {
        'processed': processed,
        'original_shape': original_shape,
        'scale_factor': scale_factor,
        'analysis': analysis  # Include analysis for detector to use
    }


def apply_adaptive_morphology(binary_image: np.ndarray, adaptive_params: dict) -> np.ndarray:
    """
    Apply morphological operations using adaptive parameters

    Parameters are tuned based on blueprint style:
    - Thin walls: smaller kernels to preserve structure
    - Thick walls: larger kernels to remove details
    - Detailed blueprints: aggressive opening to remove furniture
    - Simple blueprints: gentle processing
    """

    # OPERATION 1: Close gaps in walls (adaptive)
    close_size = adaptive_params.get('morph_close_size', 3)
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (close_size, close_size))
    closed = cv2.morphologyEx(
        binary_image,
        cv2.MORPH_CLOSE,
        kernel_close,
        iterations=1
    )
    logger.debug(f"Applied CLOSE with {close_size}x{close_size} kernel")

    # OPERATION 2: Remove details (ADAPTIVE - key parameter!)
    open_size = adaptive_params['morph_open_size']
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_size, open_size))
    opened = cv2.morphologyEx(
        closed,
        cv2.MORPH_OPEN,
        kernel_open,
        iterations=1
    )
    logger.debug(f"Applied OPEN with {open_size}x{open_size} kernel (ADAPTIVE)")

    # OPERATION 2.5: Fill hollow rooms (IMPORTANT for thick-walled CAD blueprints!)
    if adaptive_params.get('fill_hollow_rooms', False):
        logger.debug("Applying hollow room filling for thick-walled blueprint")
        opened = fill_hollow_rooms(opened)

    # OPERATION 3: Dilate to strengthen walls (adaptive)
    dilate_size = adaptive_params.get('morph_dilate_size', 2)
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (dilate_size, dilate_size))
    enhanced = cv2.dilate(
        opened,
        kernel_dilate,
        iterations=1
    )
    logger.debug(f"Applied DILATE with {dilate_size}x{dilate_size} kernel")

    return enhanced


def fill_hollow_rooms(binary_image: np.ndarray) -> np.ndarray:
    """
    Fill hollow room regions using morphological closing with large kernel

    This fixes the issue where thick-walled CAD blueprints create hollow room outlines
    instead of solid filled regions.

    Strategy:
    1. Invert image (rooms become white, walls become black)
    2. Fill holes using morphological closing with large kernel
    3. Invert back
    """

    # Invert so rooms are white
    inverted = cv2.bitwise_not(binary_image)

    # Fill small holes within rooms using morphological closing
    # Large kernel to fill room interiors without filling gaps between walls
    fill_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    filled = cv2.morphologyEx(
        inverted,
        cv2.MORPH_CLOSE,
        fill_kernel,
        iterations=2
    )

    # Invert back
    result = cv2.bitwise_not(filled)

    logger.debug("Filled hollow rooms using large kernel closing")
    return result


def decode_image(image_data: bytes) -> np.ndarray:
    """Decode image from bytes to numpy array"""
    try:
        pil_image = Image.open(BytesIO(image_data))

        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        np_image = np.array(pil_image)
        bgr_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)

        return bgr_image

    except Exception as e:
        logger.error(f"Failed to decode image: {str(e)}")
        raise ValueError(f"Unable to decode image: {str(e)}")


def resize_maintain_aspect_ratio(image: np.ndarray, max_dimension: int = 2000) -> np.ndarray:
    """Resize image maintaining aspect ratio"""
    height, width = image.shape[:2]

    if height > max_dimension or width > max_dimension:
        scale = max_dimension / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)

        resized = cv2.resize(
            image,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA
        )

        logger.info(f"Resized from {width}x{height} to {new_width}x{new_height}")
        return resized
    else:
        logger.info(f"Image already within size limit: {width}x{height}")
        return image
