#!/usr/bin/env python3
"""
Debug script to visualize what's happening in detection pipeline
"""

import cv2
import numpy as np
from pathlib import Path
from detection.preprocessing_adaptive import preprocess_pipeline_adaptive
from detection.opencv_detector_adaptive import detect_rooms_adaptive
from detection.normalizer import normalize_coordinates
import json

# Load a failing sample
sample_path = Path("../test_data/blueprints/sample_02.png")
gt_path = Path("ground_truth/sample_02_ground_truth.json")

print(f"Debugging {sample_path.name}...")

# Load image
with open(sample_path, 'rb') as f:
    image_data = f.read()

# Load ground truth
with open(gt_path, 'r') as f:
    ground_truth = json.load(f)

print(f"Ground truth has {ground_truth['total_rooms']} rooms")

# Run preprocessing
preprocessed = preprocess_pipeline_adaptive(image_data)
processed_image = preprocessed['processed']

print(f"Preprocessed image shape: {processed_image.shape}")
print(f"Preprocessed image type: {processed_image.dtype}")
print(f"Preprocessed unique values: {np.unique(processed_image)}")

# Save preprocessed image for visualization
cv2.imwrite('/tmp/preprocessed_sample_02.png', processed_image)
print("Saved preprocessed image to /tmp/preprocessed_sample_02.png")

# Find contours
contours, hierarchy = cv2.findContours(
    processed_image,
    cv2.RETR_TREE,
    cv2.CHAIN_APPROX_SIMPLE
)

print(f"\nFound {len(contours)} total contours")

# Analyze contour sizes
areas = [cv2.contourArea(c) for c in contours]
areas_sorted = sorted(areas, reverse=True)

print(f"Top 20 contour areas: {areas_sorted[:20]}")
print(f"Contours > 1000px: {sum(1 for a in areas if a > 1000)}")
print(f"Contours > 5000px: {sum(1 for a in areas if a > 5000)}")

# Run detection
detected_rooms = detect_rooms_adaptive(preprocessed)
detected_rooms = normalize_coordinates(detected_rooms, preprocessed['original_shape'])

print(f"\nDetected {len(detected_rooms)} rooms")

# Visualize on original image
original_bgr = cv2.imread(str(sample_path))
h, w = original_bgr.shape[:2]

# Draw detected rooms in blue
for room in detected_rooms:
    box = room['bounding_box_normalized']
    x1, y1, x2, y2 = int(box[0]*w), int(box[1]*h), int(box[2]*w), int(box[3]*h)
    cv2.rectangle(original_bgr, (x1, y1), (x2, y2), (255, 0, 0), 2)
    cv2.putText(original_bgr, room['id'], (x1+5, y1+20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

# Draw ground truth rooms in green
for room in ground_truth['rooms']:
    box = room['bounding_box_normalized']
    x1, y1, x2, y2 = int(box[0]*w), int(box[1]*h), int(box[2]*w), int(box[3]*h)
    cv2.rectangle(original_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2)

cv2.imwrite('/tmp/debug_sample_02_comparison.png', original_bgr)
print("Saved comparison image to /tmp/debug_sample_02_comparison.png")
print("\nBlue = Detected, Green = Ground Truth")
