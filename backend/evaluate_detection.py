#!/usr/bin/env python3
"""
Evaluation script to compare AI detection against ground truth.

Metrics:
- IoU (Intersection over Union) for bounding boxes
- Precision: % of detected rooms that match ground truth
- Recall: % of ground truth rooms that were detected
- F1 Score: harmonic mean of precision and recall
"""

import json
import os
from pathlib import Path
import cv2
import numpy as np
from detection.preprocessing_adaptive import preprocess_pipeline_adaptive
from detection.opencv_detector_adaptive import detect_rooms_adaptive
from detection.normalizer import normalize_coordinates

def calculate_iou(box1, box2):
    """
    Calculate Intersection over Union (IoU) for two bounding boxes.

    Args:
        box1, box2: [xmin, ymin, xmax, ymax] in normalized coordinates (0.0-1.0)

    Returns:
        IoU score (0.0-1.0)
    """
    # Extract coordinates
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2

    # Calculate intersection
    inter_xmin = max(x1_min, x2_min)
    inter_ymin = max(y1_min, y2_min)
    inter_xmax = min(x1_max, x2_max)
    inter_ymax = min(y1_max, y2_max)

    # Check if boxes intersect
    if inter_xmax <= inter_xmin or inter_ymax <= inter_ymin:
        return 0.0

    inter_area = (inter_xmax - inter_xmin) * (inter_ymax - inter_ymin)

    # Calculate union
    box1_area = (x1_max - x1_min) * (y1_max - y1_min)
    box2_area = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = box1_area + box2_area - inter_area

    return inter_area / union_area if union_area > 0 else 0.0


def match_rooms(ground_truth_rooms, detected_rooms, iou_threshold=0.5):
    """
    Match detected rooms to ground truth rooms using IoU threshold.

    Returns:
        matches: list of (gt_idx, det_idx, iou) tuples
        unmatched_gt: list of ground truth room indices not matched
        unmatched_det: list of detected room indices not matched (false positives)
    """
    matches = []
    matched_gt = set()
    matched_det = set()

    # Calculate IoU matrix
    iou_matrix = []
    for gt_room in ground_truth_rooms:
        gt_box = gt_room['bounding_box_normalized']
        row = []
        for det_room in detected_rooms:
            det_box = det_room['bounding_box_normalized']
            iou = calculate_iou(gt_box, det_box)
            row.append(iou)
        iou_matrix.append(row)

    # Greedy matching: match highest IoU pairs first
    while True:
        max_iou = 0.0
        max_pos = None

        for i, row in enumerate(iou_matrix):
            if i in matched_gt:
                continue
            for j, iou in enumerate(row):
                if j in matched_det:
                    continue
                if iou >= iou_threshold and iou > max_iou:
                    max_iou = iou
                    max_pos = (i, j)

        if max_pos is None:
            break

        gt_idx, det_idx = max_pos
        matches.append((gt_idx, det_idx, max_iou))
        matched_gt.add(gt_idx)
        matched_det.add(det_idx)

    # Find unmatched
    unmatched_gt = [i for i in range(len(ground_truth_rooms)) if i not in matched_gt]
    unmatched_det = [i for i in range(len(detected_rooms)) if i not in matched_det]

    return matches, unmatched_gt, unmatched_det


def evaluate_sample(ground_truth_path, image_path):
    """
    Evaluate AI detection for a single sample.

    Returns:
        metrics dict with precision, recall, f1, etc.
    """
    # Load ground truth
    with open(ground_truth_path, 'r') as f:
        ground_truth = json.load(f)

    sample_id = ground_truth['sample_id']
    gt_rooms = ground_truth['rooms']

    # Read image as bytes (required by preprocessing pipeline)
    with open(image_path, 'rb') as f:
        image_data = f.read()

    try:
        # Run detection pipeline
        preprocessed = preprocess_pipeline_adaptive(image_data)
        detected_rooms = detect_rooms_adaptive(preprocessed)

        # Normalize coordinates
        detected_rooms = normalize_coordinates(detected_rooms, preprocessed['original_shape'])
    except Exception as e:
        return {
            'sample_id': sample_id,
            'error': f'Detection failed: {str(e)}'
        }

    # Match rooms
    matches, unmatched_gt, unmatched_det = match_rooms(gt_rooms, detected_rooms)

    # Calculate metrics
    num_gt = len(gt_rooms)
    num_detected = len(detected_rooms)
    num_matched = len(matches)

    precision = num_matched / num_detected if num_detected > 0 else 0.0
    recall = num_matched / num_gt if num_gt > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # Average IoU for matches
    avg_iou = sum(match[2] for match in matches) / len(matches) if matches else 0.0

    return {
        'sample_id': sample_id,
        'num_ground_truth': num_gt,
        'num_detected': num_detected,
        'num_matched': num_matched,
        'num_false_negatives': len(unmatched_gt),
        'num_false_positives': len(unmatched_det),
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'avg_iou': avg_iou,
        'matches': [
            {
                'gt_room_id': gt_rooms[gt_idx]['id'],
                'detected_room_id': detected_rooms[det_idx].get('id', f'det_{det_idx}'),
                'iou': iou
            }
            for gt_idx, det_idx, iou in matches
        ],
        'false_negatives': [
            gt_rooms[i]['id'] for i in unmatched_gt
        ],
        'false_positives': [
            detected_rooms[i].get('id', f'det_{i}') for i in unmatched_det
        ]
    }


def main():
    """Run evaluation on all ground truth samples."""

    # Paths
    ground_truth_dir = Path(__file__).parent / 'ground_truth'
    images_dir = Path(__file__).parent.parent / 'test_data' / 'blueprints'

    # Find all ground truth files
    gt_files = sorted(ground_truth_dir.glob('*_ground_truth.json'))

    if not gt_files:
        print(f"No ground truth files found in {ground_truth_dir}")
        return

    print(f"Found {len(gt_files)} ground truth files")
    print("Using ADAPTIVE detection pipeline\n")

    # Evaluate each sample
    results = []
    for gt_file in gt_files:
        # Extract sample_id from filename (e.g., "sample_01_ground_truth.json" -> "sample_01")
        sample_id = gt_file.stem.replace('_ground_truth', '')
        image_path = images_dir / f"{sample_id}.png"

        if not image_path.exists():
            print(f"⚠️  Image not found for {sample_id}: {image_path}")
            continue

        print(f"Evaluating {sample_id}...")
        metrics = evaluate_sample(gt_file, image_path)
        results.append(metrics)

        # Print sample results
        if 'error' in metrics:
            print(f"  ❌ Error: {metrics['error']}")
        else:
            print(f"  Ground Truth: {metrics['num_ground_truth']} rooms")
            print(f"  Detected:     {metrics['num_detected']} rooms")
            print(f"  Matched:      {metrics['num_matched']} rooms")
            print(f"  Precision:    {metrics['precision']:.2%}")
            print(f"  Recall:       {metrics['recall']:.2%}")
            print(f"  F1 Score:     {metrics['f1_score']:.2%}")
            print(f"  Avg IoU:      {metrics['avg_iou']:.3f}")

            if metrics['num_false_positives'] > 0:
                print(f"  False Positives: {metrics['num_false_positives']}")
            if metrics['num_false_negatives'] > 0:
                print(f"  False Negatives: {metrics['num_false_negatives']}")

        print()

    # Calculate overall metrics
    valid_results = [r for r in results if 'error' not in r]

    if valid_results:
        print("\n" + "=" * 60)
        print("OVERALL METRICS")
        print("=" * 60)

        avg_precision = sum(r['precision'] for r in valid_results) / len(valid_results)
        avg_recall = sum(r['recall'] for r in valid_results) / len(valid_results)
        avg_f1 = sum(r['f1_score'] for r in valid_results) / len(valid_results)
        avg_iou = sum(r['avg_iou'] for r in valid_results) / len(valid_results)

        total_gt = sum(r['num_ground_truth'] for r in valid_results)
        total_detected = sum(r['num_detected'] for r in valid_results)
        total_matched = sum(r['num_matched'] for r in valid_results)
        total_fp = sum(r['num_false_positives'] for r in valid_results)
        total_fn = sum(r['num_false_negatives'] for r in valid_results)

        print(f"Samples Evaluated: {len(valid_results)}")
        print(f"Total Ground Truth Rooms: {total_gt}")
        print(f"Total Detected Rooms: {total_detected}")
        print(f"Total Matched Rooms: {total_matched}")
        print(f"Total False Positives: {total_fp}")
        print(f"Total False Negatives: {total_fn}")
        print()
        print(f"Average Precision: {avg_precision:.2%}")
        print(f"Average Recall:    {avg_recall:.2%}")
        print(f"Average F1 Score:  {avg_f1:.2%}")
        print(f"Average IoU:       {avg_iou:.3f}")
        print()

        # Identify worst performers
        print("Worst Performing Samples (by F1 Score):")
        sorted_results = sorted(valid_results, key=lambda r: r['f1_score'])
        for r in sorted_results[:3]:
            print(f"  {r['sample_id']}: F1={r['f1_score']:.2%}, "
                  f"Precision={r['precision']:.2%}, Recall={r['recall']:.2%}")

    # Save detailed results
    output_path = Path(__file__).parent / 'evaluation_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'results': results,
            'summary': {
                'num_samples': len(valid_results),
                'avg_precision': avg_precision,
                'avg_recall': avg_recall,
                'avg_f1_score': avg_f1,
                'avg_iou': avg_iou,
                'total_ground_truth': total_gt,
                'total_detected': total_detected,
                'total_matched': total_matched,
                'total_false_positives': total_fp,
                'total_false_negatives': total_fn
            }
        }, f, indent=2)

    print(f"\nDetailed results saved to: {output_path}")


if __name__ == '__main__':
    main()
