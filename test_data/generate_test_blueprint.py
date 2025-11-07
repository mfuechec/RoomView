#!/usr/bin/env python3
"""
Generate synthetic test blueprints for testing RoomView detection

Creates simple floor plan images with clear room boundaries
Useful for quick testing without downloading full CubiCasa5k dataset

Usage:
    python generate_test_blueprint.py --output blueprints/simple_3room.png
    python generate_test_blueprint.py --type complex --output blueprints/complex.png
"""

import argparse
import cv2
import numpy as np
from pathlib import Path


def generate_simple_blueprint(width=2000, height=1500):
    """
    Generate simple 3-room floor plan
    - 2 bedrooms
    - 1 hallway
    """
    # White background
    image = np.ones((height, width), dtype=np.uint8) * 255

    # Draw walls (black lines)
    wall_thickness = 10

    # Outer boundary
    cv2.rectangle(image, (100, 100), (width-100, height-100), 0, wall_thickness)

    # Room 1: Left bedroom (200x400)
    cv2.line(image, (100, 500), (700, 500), 0, wall_thickness)  # Horizontal divider
    cv2.line(image, (700, 100), (700, height-100), 0, wall_thickness)  # Vertical divider

    # Room 2: Right bedroom (300x400)
    cv2.line(image, (1300, 100), (1300, height-100), 0, wall_thickness)  # Vertical divider

    # Hallway: Center (100 wide)
    # (Already defined by the vertical dividers)

    # Add some furniture/fixtures (lighter gray)
    # Door openings (white gaps)
    cv2.line(image, (350, 100), (450, 100), 255, wall_thickness+5)  # Room 1 door
    cv2.line(image, (1450, 100), (1550, 100), 255, wall_thickness+5)  # Room 2 door

    # Windows (dashed lines)
    for x in range(200, 600, 50):
        cv2.line(image, (x, 100), (x+25, 100), 180, 3)

    return image


def generate_complex_blueprint(width=2500, height=2000):
    """
    Generate complex multi-room floor plan
    - 5 rooms
    - 2 hallways
    - Irregular shapes
    """
    image = np.ones((height, width), dtype=np.uint8) * 255
    wall_thickness = 12

    # Outer boundary
    cv2.rectangle(image, (100, 100), (width-100, height-100), 0, wall_thickness)

    # Main vertical divider
    cv2.line(image, (1200, 100), (1200, height-100), 0, wall_thickness)

    # Left side - 3 rooms stacked
    cv2.line(image, (100, 700), (1200, 700), 0, wall_thickness)
    cv2.line(image, (100, 1400), (1200, 1400), 0, wall_thickness)

    # Right side - 2 large rooms
    cv2.line(image, (1200, 1000), (width-100, 1000), 0, wall_thickness)

    # Hallway on left
    cv2.line(image, (600, 100), (600, height-100), 0, wall_thickness)

    # Add doors (white gaps)
    doors = [
        (300, 100, 380, 100),  # Top room door
        (850, 700, 930, 700),  # Middle room door
        (350, 1400, 430, 1400),  # Bottom room door
        (1450, 100, 1530, 100),  # Right top door
        (1700, 1000, 1780, 1000),  # Right bottom door
    ]

    for x1, y1, x2, y2 in doors:
        cv2.line(image, (x1, y1), (x2, y2), 255, wall_thickness+6)

    return image


def generate_office_blueprint(width=3000, height=2000):
    """
    Generate office floor plan
    - Open plan area
    - 4 private offices
    - Conference room
    - Kitchen
    """
    image = np.ones((height, width), dtype=np.uint8) * 255
    wall_thickness = 10

    # Outer boundary
    cv2.rectangle(image, (150, 150), (width-150, height-150), 0, wall_thickness)

    # Private offices along top (4 offices)
    office_width = 500
    for i in range(4):
        x = 150 + (i * office_width)
        cv2.line(image, (x, 150), (x, 650), 0, wall_thickness)
        cv2.line(image, (x, 650), (x + office_width, 650), 0, wall_thickness)

    # Conference room (right side)
    cv2.rectangle(image, (width-650, 700), (width-150, 1400), 0, wall_thickness)

    # Kitchen (right bottom)
    cv2.rectangle(image, (width-650, 1450), (width-150, height-150), 0, wall_thickness)

    # Open area is the rest (no divisions)

    # Add doors
    cv2.line(image, (300, 650), (380, 650), 255, wall_thickness+4)
    cv2.line(image, (800, 650), (880, 650), 255, wall_thickness+4)
    cv2.line(image, (1300, 650), (1380, 650), 255, wall_thickness+4)
    cv2.line(image, (1800, 650), (1880, 650), 255, wall_thickness+4)

    return image


def main():
    parser = argparse.ArgumentParser(description='Generate test blueprints')
    parser.add_argument('--type', choices=['simple', 'complex', 'office'],
                       default='simple', help='Blueprint complexity')
    parser.add_argument('--output', '-o', required=True,
                       help='Output file path')
    parser.add_argument('--width', type=int, default=2000,
                       help='Image width (default: 2000)')
    parser.add_argument('--height', type=int, default=1500,
                       help='Image height (default: 1500)')

    args = parser.parse_args()

    print(f"Generating {args.type} blueprint...")

    # Generate blueprint
    if args.type == 'simple':
        blueprint = generate_simple_blueprint(args.width, args.height)
    elif args.type == 'complex':
        blueprint = generate_complex_blueprint(args.width, args.height)
    elif args.type == 'office':
        blueprint = generate_office_blueprint(args.width, args.height)

    # Save image
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cv2.imwrite(str(output_path), blueprint)

    print(f"✅ Blueprint saved to: {output_path}")
    print(f"   Dimensions: {blueprint.shape[1]}x{blueprint.shape[0]} pixels")


if __name__ == '__main__':
    main()
