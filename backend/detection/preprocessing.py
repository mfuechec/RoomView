"""
Image Preprocessing Pipeline
Transforms raw blueprint images into optimized format for detection
"""

import cv2
import numpy as np
from io import BytesIO
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# Configuration
PREPROCESSING_CONFIG = {
    'max_dimension': 2000,
    'denoise_strength': 10,
    'contrast_clip_limit': 2.0,
    'morph_iterations': 2,
    'min_file_size': 10_000,
    'max_file_size': 10_485_760
}


def preprocess_pipeline(image_data: bytes) -> dict:
    """
    Multi-stage preprocessing pipeline
    Estimated time: 2-5 seconds

    Args:
        image_data: Raw image bytes

    Returns:
        Dictionary containing:
            - processed: Binary image ready for detection
            - original_shape: Original image dimensions (height, width)
            - scale_factor: Ratio of original to processed size

    Raises:
        ValueError: If image data is invalid
    """

    # STAGE 1: Decode & Validate (0.5s)
    logger.info("Stage 1: Decoding image")
    raw_image = decode_image(image_data)

    if raw_image is None:
        raise ValueError("Invalid image data - unable to decode")

    original_shape = raw_image.shape
    logger.info(f"Original image shape: {original_shape}")

    # STAGE 2: Resize (0.5s)
    logger.info("Stage 2: Resizing image")
    resized = resize_maintain_aspect_ratio(
        raw_image,
        max_dimension=PREPROCESSING_CONFIG['max_dimension']
    )

    # STAGE 3: Convert to Grayscale (0.2s)
    logger.info("Stage 3: Converting to grayscale")
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    # STAGE 4: Noise Reduction (0.5s)
    logger.info("Stage 4: Reducing noise")
    denoised = cv2.fastNlMeansDenoising(
        gray,
        h=PREPROCESSING_CONFIG['denoise_strength'],
        templateWindowSize=7,
        searchWindowSize=21
    )

    # STAGE 5: Contrast Enhancement (0.3s)
    logger.info("Stage 5: Enhancing contrast")
    clahe = cv2.createCLAHE(
        clipLimit=PREPROCESSING_CONFIG['contrast_clip_limit'],
        tileGridSize=(8, 8)
    )
    enhanced = clahe.apply(denoised)

    # STAGE 6: Thresholding (0.2s)
    logger.info("Stage 6: Applying threshold")
    _, binary = cv2.threshold(
        enhanced,
        0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # STAGE 7: Morphological Operations (0.5s)
    logger.info("Stage 7: Morphological operations")
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=PREPROCESSING_CONFIG['morph_iterations']
    )

    scale_factor = original_shape[0] / closed.shape[0]

    logger.info(f"Preprocessing complete. Output shape: {closed.shape}, Scale factor: {scale_factor:.2f}")

    return {
        'processed': closed,
        'original_shape': original_shape,
        'scale_factor': scale_factor
    }


def decode_image(image_data: bytes) -> np.ndarray:
    """
    Decode image from bytes to numpy array

    Args:
        image_data: Raw image bytes

    Returns:
        Image as numpy array (BGR format)

    Raises:
        ValueError: If image cannot be decoded
    """
    try:
        # Try using PIL first (handles more formats)
        pil_image = Image.open(BytesIO(image_data))

        # Convert to RGB if needed
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # Convert PIL to numpy array
        np_image = np.array(pil_image)

        # Convert RGB to BGR for OpenCV
        bgr_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)

        return bgr_image

    except Exception as e:
        logger.error(f"Failed to decode image: {str(e)}")
        raise ValueError(f"Unable to decode image: {str(e)}")


def resize_maintain_aspect_ratio(image: np.ndarray, max_dimension: int = 2000) -> np.ndarray:
    """
    Resize image maintaining aspect ratio

    Args:
        image: Input image
        max_dimension: Maximum width or height

    Returns:
        Resized image
    """
    height, width = image.shape[:2]

    # Calculate scaling factor
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
