#!/usr/bin/env python3
"""Compare detected vs ground truth boxes"""

import json
from pathlib import Path
from detection.preprocessing_adaptive import preprocess_pipeline_adaptive
from detection.opencv_detector_adaptive import detect_rooms_adaptive
from detection.normalizer import normalize_coordinates

# Load sample
sample_path = Path("../test_data/blueprints/sample_02.png")
gt_path = Path("ground_truth/sample_02_ground_truth.json")

with open(sample_path, 'rb') as f:
    image_data = f.read()

with open(gt_path, 'r') as f:
    ground_truth = json.load(f)

# Run detection
preprocessed = preprocess_pipeline_adaptive(image_data)
detected_rooms = detect_rooms_adaptive(preprocessed)
detected_rooms = normalize_coordinates(detected_rooms, preprocessed['original_shape'])

print("GROUND TRUTH ROOMS:")
print("=" * 60)
for i, room in enumerate(ground_truth['rooms'], 1):
    box = room['bounding_box_normalized']
    print(f"{i}. {room['id']}: [{box[0]:.3f}, {box[1]:.3f}, {box[2]:.3f}, {box[3]:.3f}]")
    width = box[2] - box[0]
    height = box[3] - box[1]
    print(f"   Size: {width:.3f} x {height:.3f}, Area: {width*height:.4f}")

print("\nDETECTED ROOMS:")
print("=" * 60)
for i, room in enumerate(detected_rooms, 1):
    box = room['bounding_box_normalized']
    print(f"{i}. {room['id']}: [{box[0]:.3f}, {box[1]:.3f}, {box[2]:.3f}, {box[3]:.3f}]")
    width = box[2] - box[0]
    height = box[3] - box[1]
    print(f"   Size: {width:.3f} x {height:.3f}, Area: {width*height:.4f}, Conf: {room.get('confidence_score', 0):.2f}")
