"""
Visual Comparison Tool: Original vs Improved Detection

Compares the original and improved detection pipelines side-by-side
with visual output showing detected rooms on the blueprint.

Usage:
    python compare_detectors.py path/to/blueprint.png
    python compare_detectors.py path/to/blueprint.png --show-steps
    python compare_detectors.py path/to/blueprint.png --output comparison.png
"""

import cv2
import numpy as np
import sys
import argparse
from pathlib import Path
import logging

# Import both detection pipelines
from detection.preprocessing import preprocess_pipeline
from detection.opencv_detector import detect_rooms_opencv
from detection.preprocessing_improved import preprocess_pipeline_improved
from detection.opencv_detector_improved import detect_rooms_improved
from detection.normalizer import normalize_coordinates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_image(image_path: str) -> bytes:
    """Load image file as bytes"""
    with open(image_path, 'rb') as f:
        return f.read()


def draw_rooms_on_image(image: np.ndarray, rooms: list, color_scheme: str = 'rainbow') -> np.ndarray:
    """
    Draw detected room bounding boxes on image

    Args:
        image: Input image (grayscale or color)
        rooms: List of room dictionaries with 'bounding_box' key
        color_scheme: 'rainbow', 'confidence', or 'single'

    Returns:
        Image with rooms drawn
    """

    # Convert to color if grayscale
    if len(image.shape) == 2:
        output = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        output = image.copy()

    # Generate colors
    colors = []
    if color_scheme == 'rainbow':
        for i in range(len(rooms)):
            hue = int(180 * i / max(len(rooms), 1))
            color = cv2.cvtColor(np.uint8([[[hue, 255, 255]]]), cv2.COLOR_HSV2BGR)[0][0]
            colors.append(tuple(map(int, color)))
    elif color_scheme == 'confidence':
        for room in rooms:
            conf = room.get('confidence_score', 0.5)
            # Red (low) to Green (high)
            color = (0, int(255 * conf), int(255 * (1 - conf)))
            colors.append(color)
    else:  # single color
        colors = [(0, 255, 0)] * len(rooms)

    # Draw each room
    for idx, room in enumerate(rooms):
        bbox = room['bounding_box']
        x_min, y_min, x_max, y_max = bbox

        color = colors[idx % len(colors)]

        # Draw rectangle
        cv2.rectangle(output, (x_min, y_min), (x_max, y_max), color, 2)

        # Draw label with room info
        label = f"R{idx+1}"
        if 'confidence_score' in room:
            label += f" ({room['confidence_score']:.2f})"

        # Background for text
        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(output, (x_min, y_min - text_h - 4), (x_min + text_w, y_min), color, -1)

        # Text
        cv2.putText(
            output,
            label,
            (x_min, y_min - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

    return output


def create_comparison_image(
    original_image: np.ndarray,
    original_rooms: list,
    improved_rooms: list,
    show_steps: bool = False,
    preprocessed_original: dict = None,
    preprocessed_improved: dict = None
) -> np.ndarray:
    """
    Create side-by-side comparison image

    Args:
        original_image: The original blueprint image
        original_rooms: Rooms detected by original pipeline
        improved_rooms: Rooms detected by improved pipeline
        show_steps: If True, also show preprocessing steps
        preprocessed_original: Preprocessed data from original pipeline
        preprocessed_improved: Preprocessed data from improved pipeline

    Returns:
        Comparison image
    """

    # Resize original to match processed dimensions
    processed_height = preprocessed_original['processed'].shape[0]
    processed_width = preprocessed_original['processed'].shape[1]

    resized_original = cv2.resize(original_image, (processed_width, processed_height))

    # Draw rooms on copies
    img_with_original = draw_rooms_on_image(resized_original, original_rooms, 'confidence')
    img_with_improved = draw_rooms_on_image(resized_original, improved_rooms, 'confidence')

    if show_steps:
        # Create 2x3 grid: original preprocessing, improved preprocessing, results
        proc_orig = cv2.cvtColor(preprocessed_original['processed'], cv2.COLOR_GRAY2BGR)
        proc_impr = cv2.cvtColor(preprocessed_improved['processed'], cv2.COLOR_GRAY2BGR)

        # Add titles
        proc_orig = add_title(proc_orig, "Original Preprocessing")
        proc_impr = add_title(proc_impr, "Improved Preprocessing")
        img_with_original = add_title(img_with_original, f"Original Detection ({len(original_rooms)} rooms)")
        img_with_improved = add_title(img_with_improved, f"Improved Detection ({len(improved_rooms)} rooms)")

        # Stack vertically
        row1 = np.hstack([proc_orig, proc_impr])
        row2 = np.hstack([img_with_original, img_with_improved])
        comparison = np.vstack([row1, row2])
    else:
        # Simple side-by-side
        img_with_original = add_title(img_with_original, f"Original ({len(original_rooms)} rooms)")
        img_with_improved = add_title(img_with_improved, f"Improved ({len(improved_rooms)} rooms)")
        comparison = np.hstack([img_with_original, img_with_improved])

    return comparison


def add_title(image: np.ndarray, title: str, font_scale: float = 1.0) -> np.ndarray:
    """Add title bar to top of image"""
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 2

    # Calculate text size
    (text_w, text_h), baseline = cv2.getTextSize(title, font, font_scale, thickness)

    # Create new image with title bar
    title_height = text_h + baseline + 20
    output = np.zeros((image.shape[0] + title_height, image.shape[1], 3), dtype=np.uint8)

    # Draw title background
    cv2.rectangle(output, (0, 0), (image.shape[1], title_height), (50, 50, 50), -1)

    # Draw title text
    text_x = (image.shape[1] - text_w) // 2
    text_y = text_h + 10
    cv2.putText(output, title, (text_x, text_y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

    # Copy image below title
    output[title_height:, :] = image

    return output


def print_comparison_stats(original_rooms: list, improved_rooms: list):
    """Print statistics comparing both approaches"""

    print("\n" + "="*70)
    print(" DETECTION COMPARISON STATISTICS")
    print("="*70)

    print(f"\nRooms Detected:")
    print(f"  Original Pipeline:  {len(original_rooms)} rooms")
    print(f"  Improved Pipeline:  {len(improved_rooms)} rooms")
    print(f"  Difference:         {len(improved_rooms) - len(original_rooms):+d} rooms")

    if original_rooms:
        avg_conf_orig = sum(r.get('confidence_score', 0) for r in original_rooms) / len(original_rooms)
        print(f"\nAverage Confidence (Original): {avg_conf_orig:.2f}")

    if improved_rooms:
        avg_conf_impr = sum(r.get('confidence_score', 0) for r in improved_rooms) / len(improved_rooms)
        print(f"Average Confidence (Improved): {avg_conf_impr:.2f}")

    print("\nOriginal Pipeline Rooms:")
    for i, room in enumerate(original_rooms[:10]):  # Show first 10
        print(f"  Room {i+1}: {room['area_pixels']} px² (conf: {room.get('confidence_score', 0):.2f})")
    if len(original_rooms) > 10:
        print(f"  ... and {len(original_rooms) - 10} more")

    print("\nImproved Pipeline Rooms:")
    for i, room in enumerate(improved_rooms[:10]):  # Show first 10
        print(f"  Room {i+1}: {room['area_pixels']} px² (conf: {room.get('confidence_score', 0):.2f})")
    if len(improved_rooms) > 10:
        print(f"  ... and {len(improved_rooms) - 10} more")

    print("\n" + "="*70)


def main():
    parser = argparse.ArgumentParser(description='Compare original vs improved room detection')
    parser.add_argument('image', help='Path to blueprint image')
    parser.add_argument('--show-steps', action='store_true',
                        help='Show preprocessing steps in comparison')
    parser.add_argument('--output', '-o', help='Save comparison image to file')
    parser.add_argument('--display', action='store_true',
                        help='Display comparison in window (press any key to close)')

    args = parser.parse_args()

    # Validate input
    if not Path(args.image).exists():
        logger.error(f"Image file not found: {args.image}")
        sys.exit(1)

    logger.info(f"Loading blueprint: {args.image}")
    image_data = load_image(args.image)

    # Load original image for display
    original_image = cv2.imread(args.image)
    if original_image is None:
        logger.error(f"Failed to load image: {args.image}")
        sys.exit(1)

    # Run ORIGINAL pipeline
    logger.info("="*70)
    logger.info("RUNNING ORIGINAL PIPELINE")
    logger.info("="*70)
    try:
        preprocessed_original = preprocess_pipeline(image_data)
        rooms_original = detect_rooms_opencv(preprocessed_original)
        logger.info(f"Original pipeline: Detected {len(rooms_original)} rooms")
    except Exception as e:
        logger.error(f"Original pipeline failed: {str(e)}")
        rooms_original = []
        preprocessed_original = None

    # Run IMPROVED pipeline
    logger.info("\n" + "="*70)
    logger.info("RUNNING IMPROVED PIPELINE")
    logger.info("="*70)
    try:
        preprocessed_improved = preprocess_pipeline_improved(image_data)
        rooms_improved = detect_rooms_improved(preprocessed_improved)
        logger.info(f"Improved pipeline: Detected {len(rooms_improved)} rooms")
    except Exception as e:
        logger.error(f"Improved pipeline failed: {str(e)}")
        rooms_improved = []
        preprocessed_improved = None

    # Print statistics
    print_comparison_stats(rooms_original, rooms_improved)

    # Create comparison visualization
    if preprocessed_original and preprocessed_improved:
        logger.info("\nCreating comparison visualization...")
        comparison = create_comparison_image(
            original_image,
            rooms_original,
            rooms_improved,
            show_steps=args.show_steps,
            preprocessed_original=preprocessed_original,
            preprocessed_improved=preprocessed_improved
        )

        # Save if requested
        if args.output:
            cv2.imwrite(args.output, comparison)
            logger.info(f"Saved comparison to: {args.output}")

        # Display if requested
        if args.display:
            cv2.imshow('Detection Comparison', comparison)
            logger.info("Displaying comparison (press any key to close)")
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        # Auto-save if neither specified
        if not args.output and not args.display:
            output_path = Path(args.image).stem + '_comparison.png'
            cv2.imwrite(output_path, comparison)
            logger.info(f"Saved comparison to: {output_path}")


if __name__ == '__main__':
    main()
