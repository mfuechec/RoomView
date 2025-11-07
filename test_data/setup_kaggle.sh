#!/bin/bash
# Kaggle API Setup and Blueprint Download Script
# Run this after you've downloaded kaggle.json from Kaggle

set -e  # Exit on error

echo "=================================================="
echo "🔑 Kaggle API Setup & Blueprint Download"
echo "=================================================="
echo

# Step 1: Check if kaggle.json exists in common locations
echo "Step 1: Looking for kaggle.json..."

KAGGLE_JSON=""

# Check Downloads folder
if [ -f "$HOME/Downloads/kaggle.json" ]; then
    KAGGLE_JSON="$HOME/Downloads/kaggle.json"
    echo "✓ Found in Downloads folder"
elif [ -f "$HOME/.kaggle/kaggle.json" ]; then
    KAGGLE_JSON="$HOME/.kaggle/kaggle.json"
    echo "✓ Found in ~/.kaggle/ (already installed)"
elif [ -f "./kaggle.json" ]; then
    KAGGLE_JSON="./kaggle.json"
    echo "✓ Found in current directory"
else
    echo "❌ kaggle.json not found"
    echo
    echo "Please download it first:"
    echo "1. Go to: https://www.kaggle.com/settings"
    echo "2. Scroll to 'API' section"
    echo "3. Click 'Create New API Token'"
    echo "4. Move the downloaded file to one of:"
    echo "   - ~/Downloads/kaggle.json"
    echo "   - This directory (test_data/kaggle.json)"
    echo "   - ~/.kaggle/kaggle.json"
    echo
    echo "Then run this script again."
    exit 1
fi

# Step 2: Install to ~/.kaggle/ if not already there
if [ "$KAGGLE_JSON" != "$HOME/.kaggle/kaggle.json" ]; then
    echo
    echo "Step 2: Installing kaggle.json to ~/.kaggle/..."
    mkdir -p "$HOME/.kaggle"
    cp "$KAGGLE_JSON" "$HOME/.kaggle/kaggle.json"
    echo "✓ Copied to ~/.kaggle/"
else
    echo
    echo "Step 2: Already installed in ~/.kaggle/"
fi

# Step 3: Set permissions
echo
echo "Step 3: Setting permissions..."
chmod 600 "$HOME/.kaggle/kaggle.json"
echo "✓ Permissions set (600)"

# Step 4: Verify credentials
echo
echo "Step 4: Verifying Kaggle credentials..."
if kaggle datasets list --max-size 1 &>/dev/null; then
    echo "✓ Kaggle API credentials valid!"
else
    echo "❌ Kaggle API authentication failed"
    echo "Please check your kaggle.json file contains valid credentials"
    exit 1
fi

# Step 5: Download blueprints
echo
echo "Step 5: Downloading CubiCasa5k sample blueprints..."
echo "=================================================="
echo

# Activate venv if it exists
if [ -d "../backend/venv" ]; then
    source ../backend/venv/bin/activate
    echo "✓ Virtual environment activated"
fi

# Run download script
python3 download_samples.py --num-samples 10

echo
echo "=================================================="
echo "✅ Setup Complete!"
echo "=================================================="
echo
echo "Next steps:"
echo "1. Test detection on real blueprints:"
echo "   cd ../backend"
echo "   source venv/bin/activate"
echo "   python3 test_detection_local.py --input ../test_data/blueprints/sample_01.png --visualize"
echo
echo "2. Start local server and test via UI:"
echo "   python3 local_server.py"
echo "   Then upload blueprints at http://localhost:5173"
echo
