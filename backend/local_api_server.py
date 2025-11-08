#!/usr/bin/env python3
"""
Local API Server for RoomView
Runs the detection pipeline as a REST API on localhost:3000

Usage:
    pip install flask flask-cors
    python local_api_server.py

Or use improved detection:
    USE_IMPROVED_DETECTION=true python local_api_server.py
"""

import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import logging

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Detection mode selection
# USE_ADAPTIVE_DETECTION=true  - Adaptive (auto-adjusts to blueprint style) - DEFAULT
# USE_ADAPTIVE_DETECTION=false - Improved (fixed parameters, hierarchical analysis)
USE_ADAPTIVE = os.environ.get('USE_ADAPTIVE_DETECTION', 'true').lower() == 'true'

if USE_ADAPTIVE:
    print("✨ Using ADAPTIVE detection pipeline (auto-tuning for each blueprint)")
    from detection.preprocessing_adaptive import preprocess_pipeline_adaptive as preprocess_pipeline
    from detection.opencv_detector_adaptive import detect_rooms_adaptive as detect_rooms_opencv
else:
    print("🚀 Using IMPROVED detection pipeline (fixed parameters)")
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Configuration
PORT = int(os.environ.get('PORT', 3000))


@app.route('/detect', methods=['POST'])
def detect():
    """
    Main detection endpoint
    Accepts multipart/form-data with 'blueprint' file
    """
    start_time = time.time()
    preprocessed = None  # Initialize for error handling

    try:
        logger.info("Detection request received")

        # Extract file from request
        if 'blueprint' not in request.files:
            return jsonify(error_response(
                400,
                'MISSING_FILE',
                'No blueprint file provided. Expected multipart/form-data with field "blueprint"'
            )), 400

        file = request.files['blueprint']

        if file.filename == '':
            return jsonify(error_response(
                400,
                'EMPTY_FILENAME',
                'No file selected'
            )), 400

        # Read file data
        image_data = file.read()
        logger.info(f"Received file: {file.filename} ({len(image_data)} bytes)")

        # Validate image
        try:
            validate_image_data(image_data)
        except ImageValidationError as e:
            logger.warning(f"Validation failed: {str(e)}")
            return jsonify(error_response(422, 'INVALID_IMAGE', str(e))), 422

        # STEP 1: Preprocess
        logger.info("Starting preprocessing")
        preprocessed = preprocess_pipeline(image_data)

        # STEP 2: Detect rooms
        logger.info("Starting detection")
        rooms = detect_rooms_opencv(preprocessed)

        if not rooms:
            raise DetectionFailedError("No rooms detected in blueprint")

        # STEP 3: Normalize coordinates
        logger.info(f"Normalizing {len(rooms)} rooms")
        # Use PROCESSED shape because bounding boxes are in resized image coordinates
        processed_shape = preprocessed['processed'].shape
        normalized_rooms = normalize_coordinates(
            rooms,
            processed_shape
        )

        # Build response
        processing_time = time.time() - start_time

        # Collect metrics
        blueprint_style = normalized_rooms[0].get('blueprint_style', 'unknown') if normalized_rooms else 'unknown'
        avg_confidence = sum(r['confidence_score'] for r in normalized_rooms) / len(normalized_rooms) if normalized_rooms else 0

        # Log structured metrics for analytics
        logger.info(
            f"METRICS: "
            f"rooms={len(normalized_rooms)} "
            f"style={blueprint_style} "
            f"time={processing_time:.2f}s "
            f"resolution={preprocessed['original_shape'][1]}x{preprocessed['original_shape'][0]} "
            f"avg_confidence={avg_confidence:.2f} "
            f"mode={'adaptive' if USE_ADAPTIVE else 'improved'}"
        )

        response = {
            'status': 'success',
            'blueprint_id': f"bp_{int(time.time())}",
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

        logger.info(f"✅ Detection complete: {len(rooms)} rooms in {processing_time:.2f}s")

        return jsonify(response), 200

    except DetectionFailedError as e:
        logger.warning(f"Detection failed: {str(e)}")

        # Generate smart suggestions based on image characteristics
        suggestions = []
        if preprocessed:
            img_shape = preprocessed['processed'].shape
            original_shape = preprocessed['original_shape']

            # Check image resolution
            if original_shape[0] < 800 or original_shape[1] < 800:
                suggestions.append("Image resolution is low (< 800px). Try a higher resolution scan")

            # Check if image was heavily resized
            scale_factor = preprocessed.get('scale_factor', 1)
            if scale_factor > 2:
                suggestions.append(f"Image was heavily downscaled ({scale_factor:.1f}x). Original detail may be lost")

            # Get style analysis if available
            if 'analysis' in preprocessed:
                style = preprocessed['analysis'].get('style')
                contrast = preprocessed['analysis'].get('contrast_level', 0)

                if contrast < 0.3:
                    suggestions.append("Low contrast detected. Try scanning with higher contrast settings")

                if style == 'scanned':
                    suggestions.append("Scanned blueprint detected. Ensure scan is clean without artifacts")

        # Add general suggestions
        if not suggestions:
            suggestions = [
                "Ensure blueprint has clear, continuous wall lines",
                "Try a higher resolution image (recommended: 1500x1500px or larger)",
                "Verify blueprint is not a multi-floor plan (process each floor separately)"
            ]

        return jsonify(error_response(
            422,
            'NO_ROOMS_FOUND',
            str(e),
            suggestions=suggestions
        )), 422

    except Exception as e:
        logger.exception("Unexpected error")
        return jsonify(error_response(
            500,
            'INTERNAL_ERROR',
            f"An unexpected error occurred: {str(e)}"
        )), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'detection_mode': 'adaptive' if USE_ADAPTIVE else 'improved',
        'timestamp': time.time()
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API info"""
    return jsonify({
        'service': 'RoomView Local API',
        'detection_mode': 'adaptive' if USE_ADAPTIVE else 'improved',
        'endpoints': {
            'POST /detect': 'Upload blueprint and detect rooms',
            'GET /health': 'Health check',
        },
        'usage': 'Send multipart/form-data with field "blueprint" to /detect'
    }), 200


if __name__ == '__main__':
    print("\n" + "="*70)
    print(" 🏠 RoomView Local API Server")
    print("="*70)
    print(f"\n Detection Mode: {'ADAPTIVE ✨' if USE_ADAPTIVE else 'IMPROVED 🚀'}")
    print(f" Server URL:     http://localhost:{PORT}")
    print(f" Detect Endpoint: http://localhost:{PORT}/detect")
    print(f" Health Check:   http://localhost:{PORT}/health")
    print("\n" + "="*70)
    print("\n 📡 Starting server...\n")

    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=True,
        threaded=True
    )
