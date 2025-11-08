"""
RoomView Lambda Function - Main Entry Point
Handles blueprint upload and room detection requests
"""

import json
import logging
import base64
import time
import os
from typing import Dict, Any

# Toggle between detection modes
# USE_ADAPTIVE_DETECTION=true  - Adaptive (auto-adjusts to blueprint style) - DEFAULT
# USE_ADAPTIVE_DETECTION=false - Improved (fixed parameters, hierarchical analysis)
USE_ADAPTIVE = os.environ.get('USE_ADAPTIVE_DETECTION', 'true').lower() == 'true'

# Local imports - conditional based on mode
if USE_ADAPTIVE:
    logger = logging.getLogger()
    logger.info("Using ADAPTIVE detection pipeline (auto-tuning)")
    from detection.preprocessing_adaptive import preprocess_pipeline_adaptive as preprocess_pipeline
    from detection.opencv_detector_adaptive import detect_rooms_adaptive as detect_rooms_opencv
else:
    logger = logging.getLogger()
    logger.info("Using IMPROVED detection pipeline (fixed parameters)")
    from detection.preprocessing_improved import preprocess_pipeline_improved as preprocess_pipeline
    from detection.opencv_detector_improved import detect_rooms_improved as detect_rooms_opencv

from detection.normalizer import normalize_coordinates
from utils.validation import validate_image_data
from utils.error_handling import (
    error_response,
    ImageValidationError,
    DetectionFailedError
)

# Configure logging
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for room detection

    Args:
        event: API Gateway event containing blueprint image
        context: Lambda context with runtime info

    Returns:
        API Gateway response with detected rooms or error
    """
    start_time = time.time()

    try:
        logger.info("Room detection started", extra={
            'request_id': context.request_id,
            'remaining_time_ms': context.get_remaining_time_in_millis()
        })

        # Extract and decode image from request
        image_data = extract_image_from_event(event)

        # Validate image
        validate_image_data(image_data)

        # STEP 1: Preprocess image
        logger.info("Starting preprocessing")
        preprocessed = preprocess_pipeline(image_data)

        # STEP 2: Detect rooms using OpenCV
        logger.info("Starting room detection")
        rooms = detect_rooms_opencv(preprocessed)

        if not rooms:
            raise DetectionFailedError("No rooms detected in blueprint")

        # STEP 3: Normalize coordinates
        logger.info(f"Normalizing coordinates for {len(rooms)} rooms")
        # Use PROCESSED shape because bounding boxes are in resized image coordinates
        processed_shape = preprocessed['processed'].shape
        normalized_rooms = normalize_coordinates(
            rooms,
            processed_shape
        )

        # Build success response with metrics
        processing_time = time.time() - start_time

        # Collect metrics
        blueprint_style = normalized_rooms[0].get('blueprint_style', 'unknown') if normalized_rooms else 'unknown'
        avg_confidence = sum(r['confidence_score'] for r in normalized_rooms) / len(normalized_rooms) if normalized_rooms else 0

        # Log structured metrics for CloudWatch analytics
        logger.info(
            f"METRICS: "
            f"rooms={len(normalized_rooms)} "
            f"style={blueprint_style} "
            f"time={processing_time:.2f}s "
            f"resolution={preprocessed['original_shape'][1]}x{preprocessed['original_shape'][0]} "
            f"avg_confidence={avg_confidence:.2f} "
            f"mode={'adaptive' if USE_ADAPTIVE else 'improved'}",
            extra={
                'rooms_detected': len(normalized_rooms),
                'processing_time': processing_time,
                'blueprint_style': blueprint_style,
                'avg_confidence': avg_confidence
            }
        )

        response_body = {
            'status': 'success',
            'blueprint_id': f"bp_{int(time.time())}_{context.request_id[:8]}",
            'processing_time_seconds': round(processing_time, 2),
            'image_dimensions': {
                'width_pixels': preprocessed['original_shape'][1],
                'height_pixels': preprocessed['original_shape'][0]
            },
            'total_rooms_detected': len(normalized_rooms),
            'detection_metadata': {
                'blueprint_style': blueprint_style,
                'detection_mode': 'adaptive' if USE_ADAPTIVE else 'improved',
                'average_confidence': round(avg_confidence, 2)
            },
            'rooms': normalized_rooms
        }

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'X-Processing-Time': str(int(processing_time * 1000))
            },
            'body': json.dumps(response_body)
        }

    except ImageValidationError as e:
        logger.warning(f"Image validation failed: {str(e)}")
        return error_response(
            422,
            'INVALID_IMAGE',
            str(e)
        )

    except DetectionFailedError as e:
        logger.warning(f"Detection failed: {str(e)}")
        return error_response(
            422,
            'NO_ROOMS_FOUND',
            str(e),
            suggestions=[
                "Ensure blueprint has clear wall lines",
                "Try a higher resolution scan",
                "Remove handwritten annotations if possible"
            ]
        )

    except TimeoutError as e:
        logger.error(f"Processing timeout: {str(e)}")
        return error_response(
            504,
            'TIMEOUT',
            "Processing exceeded 30-second limit. Try a smaller image."
        )

    except Exception as e:
        logger.exception("Unexpected error in lambda_handler")
        return error_response(
            500,
            'INTERNAL_ERROR',
            "An unexpected error occurred during processing",
            request_id=context.request_id
        )


def extract_image_from_event(event: Dict[str, Any]) -> bytes:
    """
    Extract image data from API Gateway event

    Args:
        event: API Gateway event

    Returns:
        Raw image bytes

    Raises:
        ImageValidationError: If image data is missing or invalid
    """
    try:
        # Handle base64 encoded body from API Gateway
        body = event.get('body', '')

        if event.get('isBase64Encoded', False):
            image_data = base64.b64decode(body)
        else:
            # If not base64 encoded, assume it's already binary
            image_data = body.encode() if isinstance(body, str) else body

        if not image_data:
            raise ImageValidationError("No image data provided in request")

        return image_data

    except Exception as e:
        raise ImageValidationError(f"Failed to extract image from request: {str(e)}")
