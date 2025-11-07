"""
Download sample blueprints from CubiCasa5k dataset

Prerequisites:
1. Install Kaggle API: pip install kaggle
2. Setup Kaggle credentials: https://www.kaggle.com/docs/api
   - Download kaggle.json from your Kaggle account
   - Place in ~/.kaggle/kaggle.json
   - chmod 600 ~/.kaggle/kaggle.json

Usage:
    python download_samples.py --num-samples 10
"""

import os
import argparse
import shutil
from pathlib import Path


def download_dataset():
    """Download CubiCasa5k dataset using Kaggle API"""
    print("Downloading CubiCasa5k dataset...")
    os.system("kaggle datasets download -d emarva/cubicasa5k")
    print("Download complete!")


def extract_samples(num_samples=10):
    """Extract a subset of blueprints for testing"""
    import zipfile

    dataset_zip = "cubicasa5k.zip"

    if not os.path.exists(dataset_zip):
        print("Dataset not found. Downloading...")
        download_dataset()

    print(f"Extracting {num_samples} sample blueprints...")

    with zipfile.ZipFile(dataset_zip, 'r') as zip_ref:
        # Get list of image files
        image_files = [f for f in zip_ref.namelist() if f.endswith(('.png', '.jpg', '.jpeg'))]

        # Take first num_samples
        samples = image_files[:num_samples]

        # Extract to blueprints directory
        for i, sample in enumerate(samples, 1):
            zip_ref.extract(sample, 'temp/')

            # Copy to blueprints folder with clean name
            src = os.path.join('temp', sample)
            dst = f'blueprints/sample_{i:02d}.png'
            shutil.copy(src, dst)

            # Also copy to frontend public folder
            frontend_dst = f'../frontend/public/sample_blueprints/sample_{i:02d}.png'
            shutil.copy(src, frontend_dst)

            print(f"  ✓ Extracted: {sample} → sample_{i:02d}.png")

    # Cleanup
    shutil.rmtree('temp', ignore_errors=True)

    print(f"\n✅ {num_samples} samples ready in:")
    print(f"   - test_data/blueprints/")
    print(f"   - frontend/public/sample_blueprints/")


def main():
    parser = argparse.ArgumentParser(description='Download CubiCasa5k samples')
    parser.add_argument('--num-samples', type=int, default=10,
                      help='Number of samples to extract (default: 10)')
    parser.add_argument('--download-only', action='store_true',
                      help='Only download, don\'t extract')

    args = parser.parse_args()

    if args.download_only:
        download_dataset()
    else:
        extract_samples(args.num_samples)


if __name__ == '__main__':
    main()
