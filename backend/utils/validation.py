"""
Input Validation
Validates blueprint image data before processing
"""

import logging

logger = logging.getLogger(__name__)

# Validation configuration
MIN_FILE_SIZE = 10_000        # 10 KB
MAX_FILE_SIZE = 10_485_760    # 10 MB


class ImageValidationError(Exception):
    """Raised when image validation fails"""
    pass


def validate_image_data(image_data: bytes) -> None:
    """
    Validate image data before processing

    Args:
        image_data: Raw image bytes

    Raises:
        ImageValidationError: If validation fails
    """

    # Check if data exists
    if not image_data:
        raise ImageValidationError("No image data provided")

    # Check file size
    file_size = len(image_data)

    if file_size < MIN_FILE_SIZE:
        raise ImageValidationError(
            f"File too small ({file_size} bytes). Minimum size is {MIN_FILE_SIZE} bytes."
        )

    if file_size > MAX_FILE_SIZE:
        raise ImageValidationError(
            f"File too large ({file_size / 1024 / 1024:.1f} MB). Maximum size is 10 MB."
        )

    # Check for valid image file signatures (magic bytes)
    if not is_valid_image_format(image_data):
        raise ImageValidationError(
            "Unsupported file format. Please upload PNG, JPG, or PDF."
        )

    logger.info(f"Image validation passed: {file_size / 1024:.1f} KB")


def is_valid_image_format(image_data: bytes) -> bool:
    """
    Check if image data has valid file signature (magic bytes)

    Args:
        image_data: Raw image bytes

    Returns:
        True if format is supported (PNG, JPG, PDF)
    """

    if len(image_data) < 8:
        return False

    # PNG signature
    if image_data[:8] == b'\x89PNG\r\n\x1a\n':
        return True

    # JPEG signature
    if image_data[:2] == b'\xff\xd8':
        return True

    # PDF signature
    if image_data[:4] == b'%PDF':
        return True

    return False
