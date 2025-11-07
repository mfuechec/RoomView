# RoomView Test Data

This directory contains test blueprints for validating the room detection algorithm.

## Current Status

✅ **Synthetic Blueprints Generated** (3 files in `blueprints/`)
- `simple.png` - Basic 3-room layout
- `complex.png` - Multi-room with hallways
- `office.png` - Office layout with cubicles

✅ **Detection Tested Locally**
- Processing time: 0.27-0.39 seconds
- Successfully detecting 2-3 rooms per blueprint
- Visualization working

⏳ **Next: Download Real Blueprints from CubiCasa5k**

## Quick Start: Download Real Blueprints

### Option 1: Automated Setup (Recommended)

```bash
# 1. Download kaggle.json from Kaggle
#    Go to: https://www.kaggle.com/settings
#    Click "Create New API Token" in the API section
#    This downloads kaggle.json to your Downloads folder

# 2. Run the automated setup script
cd /Users/mfuechec/Desktop/GauntletProjects/RoomView/test_data
./setup_kaggle.sh
```

The script will automatically:
- Find your kaggle.json file (in Downloads, current dir, or ~/.kaggle/)
- Install it to ~/.kaggle/ with correct permissions (600)
- Verify your Kaggle credentials work
- Download 10 professional blueprint samples from CubiCasa5k
- Copy them to frontend for UI testing

### Option 2: Manual Setup

Follow the detailed step-by-step instructions in `KAGGLE_SETUP.md`

### Option 3: Manual Download from Web

1. Go to https://www.kaggle.com/datasets/emarva/cubicasa5k
2. Click "Download" (5 GB zip file)
3. Extract and copy 5-10 sample PNG files to `blueprints/` folder
4. Copy the same files to `../frontend/public/sample_blueprints/`

## Directory Structure

```
test_data/
├── blueprints/              # Test blueprints for backend testing
│   ├── sample_01.png
│   ├── sample_02.png
│   └── ...
├── expected_results/        # Expected detection outputs (for validation)
│   ├── sample_01_expected.json
│   └── ...
└── download_samples.py      # Automated download script
```

## Testing Detection

### Test on Synthetic Blueprints (Already Working!)

```bash
cd ../backend
source venv/bin/activate

# Test with visualization
python3 test_detection_local.py \
  --input ../test_data/blueprints/simple.png \
  --visualize

# Test other samples
python3 test_detection_local.py --input ../test_data/blueprints/complex.png --visualize
python3 test_detection_local.py --input ../test_data/blueprints/office.png --visualize
```

Expected results:
- **simple.png**: 2-3 rooms detected, ~0.27s processing
- **complex.png**: 3-4 rooms detected, ~0.39s processing
- **office.png**: 2-3 rooms detected, ~0.31s processing

### Test on Real Blueprints (After Download)

```bash
python3 test_detection_local.py \
  --input ../test_data/blueprints/sample_01.png \
  --visualize
```

### Test via Web UI

1. **Start backend server:**
   ```bash
   cd ../backend
   source venv/bin/activate
   python3 local_server.py
   ```
   Server runs at: http://localhost:3000

2. **Start frontend:**
   ```bash
   cd ../frontend
   npm run dev
   ```
   UI available at: http://localhost:5173

3. **Upload blueprint:** Drag & drop any file from `test_data/blueprints/`

## Dataset Information

**CubiCasa5k:**
- 5000 floor plan images
- 80+ room categories
- Polygon annotations for precise boundaries
- Real-world architectural drawings

**Why this dataset is perfect:**
- Professional CAD blueprints (clean lines)
- Variety of room layouts
- Multiple floor plan styles
- Ground truth annotations for validation

## Creating Expected Results

To create validation fixtures:

```python
# Run detection on sample
python backend/test_detection_local.py \
  --input test_data/blueprints/sample_01.png \
  --output test_data/expected_results/sample_01_expected.json
```

Then manually verify and adjust the results if needed.

## Troubleshooting

### "kaggle.json not found"

The setup script looks for kaggle.json in these locations:
1. `~/Downloads/kaggle.json`
2. Current directory (`test_data/kaggle.json`)
3. `~/.kaggle/kaggle.json`

**Solution:**
- Download from https://www.kaggle.com/settings (click "Create New API Token")
- Move/copy the file to one of the above locations
- Run `./setup_kaggle.sh` again

### "401 Unauthorized" Error

**Check permissions:**
```bash
ls -la ~/.kaggle/kaggle.json
# Should show: -rw------- (chmod 600)
```

**Verify file contents:**
```bash
cat ~/.kaggle/kaggle.json
# Should be valid JSON: {"username":"...","key":"..."}
```

**Make sure you're logged in:**
- Visit https://www.kaggle.com and sign in
- API token must match your logged-in account

### Detection Not Finding Rooms

- Try synthetic blueprints first (`simple.png`, `complex.png`) - these always work
- Use `--visualize` flag to see preprocessing steps
- Some real blueprints may be too complex or low-quality
- Check that input file is a clear floor plan (not a photo)

## Blueprint Quality Notes

- **File size:** 1-5 MB per blueprint
- **Resolution:** 2000-4000 pixels wide recommended
- **Format:** PNG (preferred), JPG, or PDF
- **Quality:** Clean lines, high contrast, architectural drawings work best

For the MVP, **5-10 diverse samples** is sufficient to demonstrate:
- Simple rectangular rooms ✓
- Complex irregular layouts ✓
- Hallways and corridors ✓
- Multi-room apartments ✓
- Large office spaces ✓
