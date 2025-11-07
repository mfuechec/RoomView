#!/usr/bin/env python3
"""
Local testing script for room detection algorithm

Tests the complete pipeline without AWS Lambda:
1. Load blueprint image
2. Preprocess
3. Detect rooms
4. Normalize coordinates
5. Display results

Usage:
    python test_detection_local.py --input ../test_data/blueprints/sample_01.png
    python test_detection_local.py --input ../test_data/blueprints/sample_01.png --output results.json
    python test_detection_local.py --input ../test_data/blueprints/sample_01.png --visualize
"""

import argparse
import json
import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import cv2
import numpy as np
from detection.preprocessing import preprocess_pipeline
from detection.opencv_detector import detect_rooms_opencv
from detection.normalizer import normalize_coordinates


def load_image(image_path: str) -> np.ndarray:
    """Load image from file"""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Failed to load image: {image_path}")
    return image


def visualize_results(image_path: str, rooms: list):
    """
    Visualize detected rooms on the original blueprint
    Saves output as <original>_detected.png
    """
    # Load original image
    image = cv2.imread(image_path)
    height, width = image.shape[:2]

    # Create overlay
    overlay = image.copy()

    for room in rooms:
        # Get pixel coordinates
        x_min, y_min, x_max, y_max = room['bounding_box_pixels']

        # Choose color based on type
        if room.get('type_hint') == 'hallway':
            color = (255, 165, 0)  # Orange
        elif room.get('isUserCreated'):
            color = (0, 0, 255)    # Red
        else:
            color = (0, 255, 0)    # Green

        # Draw bounding box
        cv2.rectangle(overlay, (x_min, y_min), (x_max, y_max), color, 3)

        # Draw room ID
        label = f"{room['id']}"
        if room.get('confidence_score'):
            label += f" ({room['confidence_score']:.2f})"

        cv2.putText(overlay, label, (x_min + 5, y_min + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    # Save result
    output_path = str(Path(image_path).parent / f"{Path(image_path).stem}_detected.png")
    cv2.imwrite(output_path, overlay)
    print(f"\n✅ Visualization saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Test room detection locally')
    parser.add_argument('--input', '-i', required=True,
                       help='Path to blueprint image')
    parser.add_argument('--output', '-o',
                       help='Path to save JSON results (optional)')
    parser.add_argument('--visualize', '-v', action='store_true',
                       help='Create visualization with detected rooms')
    parser.add_argument('--verbose', action='store_true',
                       help='Print detailed logs')

    args = parser.parse_args()

    print("=" * 60)
    print("RoomView Local Detection Test")
    print("=" * 60)

    # Load image
    print(f"\n📁 Loading image: {args.input}")
    try:
        image = load_image(args.input)
        print(f"   ✓ Image loaded: {image.shape[1]}x{image.shape[0]} pixels")
    except Exception as e:
        print(f"   ✗ Error loading image: {e}")
        return 1

    # Convert to bytes (simulate API upload)
    _, encoded = cv2.imencode('.png', image)
    image_bytes = encoded.tobytes()

    print(f"\n⚙️  Running detection pipeline...")
    start_time = time.time()

    try:
        # STEP 1: Preprocessing
        print("   [1/3] Preprocessing...")
        preprocessed = preprocess_pipeline(image_bytes)
        print(f"      ✓ Preprocessed to {preprocessed['processed'].shape}")

        # STEP 2: Detection
        print("   [2/3] Detecting rooms...")
        rooms = detect_rooms_opencv(preprocessed)
        print(f"      ✓ Detected {len(rooms)} potential rooms")

        # STEP 3: Normalization
        print("   [3/3] Normalizing coordinates...")
        normalized_rooms = normalize_coordinates(rooms, preprocessed['original_shape'])
        print(f"      ✓ Normalized coordinates")

        processing_time = time.time() - start_time

    except Exception as e:
        print(f"   ✗ Detection failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Build result
    result = {
        'status': 'success',
        'processing_time_seconds': round(processing_time, 2),
        'image_dimensions': {
            'width_pixels': preprocessed['original_shape'][1],
            'height_pixels': preprocessed['original_shape'][0]
        },
        'total_rooms_detected': len(normalized_rooms),
        'rooms': normalized_rooms
    }

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"✅ Detection Complete!")
    print(f"{'=' * 60}")
    print(f"Processing Time: {processing_time:.2f}s")
    print(f"Rooms Detected:  {len(normalized_rooms)}")
    print()

    # Print room details
    if normalized_rooms:
        print("Detected Rooms:")
        print("-" * 60)
        for room in normalized_rooms:
            print(f"  {room['id']:12s} | "
                  f"{room.get('type_hint', 'unknown'):8s} | "
                  f"confidence: {room.get('confidence_score', 0):.2f} | "
                  f"area: {room.get('area_normalized', 0):.4f}")
        print()

    # Save JSON output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"💾 Results saved to: {args.output}")

    # Create visualization
    if args.visualize:
        print("\n🎨 Creating visualization...")
        visualize_results(args.input, normalized_rooms)

    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
