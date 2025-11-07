#!/usr/bin/env python3
"""
Local development server for RoomView backend

Runs a Flask server that wraps the Lambda function logic
Allows testing detection without deploying to AWS

Usage:
    python local_server.py

Then access at: http://localhost:3000
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lambda_function import lambda_handler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Mock Lambda context
class MockContext:
    def __init__(self):
        self.request_id = 'local-dev-request'
        self.function_name = 'RoomViewDetector-Local'
        self.memory_limit_in_mb = 2048
        self.invoked_function_arn = 'arn:aws:lambda:local:000000000000:function:RoomViewDetector'

    def get_remaining_time_in_millis(self):
        return 30000  # 30 seconds


@app.route('/detect', methods=['POST', 'OPTIONS'])
def detect_rooms():
    """
    Handle room detection requests
    Mimics API Gateway + Lambda behavior
    """

    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204

    try:
        # Get uploaded file
        if 'blueprint' not in request.files:
            return jsonify({
                'status': 'error',
                'error_code': 'NO_FILE',
                'message': 'No blueprint file provided'
            }), 400

        file = request.files['blueprint']

        if file.filename == '':
            return jsonify({
                'status': 'error',
                'error_code': 'NO_FILE',
                'message': 'No file selected'
            }), 400

        # Read file data
        file_data = file.read()

        logger.info(f"Received upload: {file.filename} ({len(file_data)} bytes)")

        # Convert to Lambda event format
        import base64
        event = {
            'body': base64.b64encode(file_data).decode('utf-8'),
            'isBase64Encoded': True,
            'headers': {
                'Content-Type': file.content_type or 'image/png'
            }
        }

        # Create mock context
        context = MockContext()

        # Call Lambda handler
        logger.info("Processing with Lambda handler...")
        response = lambda_handler(event, context)

        # Parse response
        status_code = response.get('statusCode', 500)
        body = response.get('body', '{}')

        # Return response
        import json
        response_data = json.loads(body)

        return jsonify(response_data), status_code

    except Exception as e:
        logger.exception("Error processing request")
        return jsonify({
            'status': 'error',
            'error_code': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'RoomView Local Server',
        'version': '1.0.0'
    })


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API info"""
    return jsonify({
        'service': 'RoomView API (Local)',
        'version': '1.0.0',
        'endpoints': {
            'POST /detect': 'Upload blueprint and detect rooms',
            'GET /health': 'Health check'
        },
        'docs': 'See README.md for usage instructions'
    })


if __name__ == '__main__':
    print("=" * 60)
    print("🏗️  RoomView Local Development Server")
    print("=" * 60)
    print()
    print("Server running at: http://localhost:3000")
    print("API endpoint:      http://localhost:3000/detect")
    print()
    print("To test from frontend:")
    print("  1. Set USE_MOCK_API = false in BlueprintUploader.jsx")
    print("  2. Ensure VITE_API_URL=http://localhost:3000 in .env")
    print("  3. Upload a blueprint in the UI")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    # Run server
    app.run(host='0.0.0.0', port=3000, debug=True)
