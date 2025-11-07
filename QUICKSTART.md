# RoomView - Quick Start Guide

Get RoomView running in **15 minutes** with test blueprints.

## 🚀 3-Step Quick Start

### Step 1: Generate Test Blueprints (2 minutes)

```bash
cd test_data

# Generate simple 3-room blueprint
python generate_test_blueprint.py --type simple --output blueprints/simple.png

# Generate complex multi-room blueprint
python generate_test_blueprint.py --type complex --output blueprints/complex.png

# Generate office floor plan
python generate_test_blueprint.py --type office --output blueprints/office.png
```

You'll now have 3 test blueprints in `test_data/blueprints/`

---

### Step 2: Test Backend Detection (5 minutes)

```bash
cd ../backend

# Install dependencies
pip install -r requirements.txt

# Test detection on simple blueprint
python test_detection_local.py \
  --input ../test_data/blueprints/simple.png \
  --visualize

# Check the output
# → Creates simple_detected.png showing detected rooms
```

**Expected output:**
```
✅ Detection Complete!
Processing Time: 3.2s
Rooms Detected:  3

Detected Rooms:
  room_001     | room     | confidence: 0.95 | area: 0.1250
  room_002     | room     | confidence: 0.92 | area: 0.1875
  hallway_001  | hallway  | confidence: 0.78 | area: 0.0625

✅ Visualization saved to: ../test_data/blueprints/simple_detected.png
```

---

### Step 3: Run Frontend (5 minutes)

```bash
cd ../frontend

# Install dependencies (if not done)
npm install

# Start dev server
npm run dev
```

Open **http://localhost:5173/** and:
1. Drag & drop one of your test blueprints
2. Wait for processing (uses mock API - returns in 2 seconds)
3. See rooms displayed on canvas
4. Click rooms to select, × to delete
5. Export JSON

---

## 🎯 Alternative: Use Real CubiCasa5k Data (30 minutes)

### Download Professional Blueprints

```bash
cd test_data

# Setup Kaggle credentials (one-time)
# 1. Go to https://www.kaggle.com/settings
# 2. Create API token → downloads kaggle.json
# 3. Move to ~/.kaggle/
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Install Kaggle API
pip install kaggle

# Download 10 samples from CubiCasa5k
python download_samples.py --num-samples 10
```

This downloads **real architectural floor plans** with:
- Professional CAD quality
- Variety of layouts
- Multiple room types
- Complex irregular shapes

Then test with:
```bash
cd ../backend
python test_detection_local.py \
  --input ../test_data/blueprints/sample_01.png \
  --visualize
```

---

## 📊 Understanding Results

### Detection Output Format

```json
{
  "status": "success",
  "processing_time_seconds": 18.42,
  "total_rooms_detected": 8,
  "rooms": [
    {
      "id": "room_001",
      "bounding_box_normalized": [0.125, 0.083, 0.375, 0.533],
      "bounding_box_pixels": [300, 150, 900, 960],
      "confidence_score": 0.92,
      "type_hint": "room",
      "area_normalized": 0.1125
    }
  ]
}
```

### Confidence Scores

- **0.9 - 1.0**: Excellent detection (clear rectangular room)
- **0.7 - 0.9**: Good detection (may have minor irregularities)
- **0.5 - 0.7**: Fair detection (irregular shape or small room)
- **< 0.5**: Low confidence (may be false positive)

---

## 🧪 Testing Checklist

Before deploying to AWS, verify locally:

- [ ] Simple blueprint: Detects 3 rooms correctly
- [ ] Complex blueprint: Detects 5+ rooms
- [ ] Processing time: < 30 seconds
- [ ] No crashes on large images (3000x2000 px)
- [ ] Handles irregular room shapes
- [ ] Filters out closets/small spaces
- [ ] Frontend displays results correctly
- [ ] Export JSON works

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'cv2'"

```bash
pip install opencv-python-headless
```

### "No rooms detected" on test blueprints

Check detection thresholds in `backend/detection/opencv_detector.py`:
```python
DETECTION_CONFIG = {
    'min_room_area_pixels': 1500,  # Lower this if rooms too small
    'canny_low_threshold': 50,      # Adjust for edge detection
}
```

### Frontend shows "Network Error"

You're using the mock API which is perfect for testing. To use real backend:
1. Deploy Lambda (see main README.md)
2. Update `frontend/.env`: `VITE_API_URL=<your-api-url>`

### Processing takes > 30 seconds

Reduce image size in preprocessing:
```python
# backend/detection/preprocessing.py
PREPROCESSING_CONFIG = {
    'max_dimension': 1500,  # Was 2000
}
```

---

## 🚀 Next Steps

Once local testing works:

1. **Deploy Backend** → See `backend/README.md`
2. **Deploy Frontend** → See `frontend/README.md`
3. **End-to-End Test** → Upload real blueprint via UI
4. **Demo Prep** → Prepare 3-5 sample blueprints for presentation

---

## 📁 File Locations

After quick start, you'll have:

```
RoomView/
├── test_data/
│   ├── blueprints/
│   │   ├── simple.png              ✅ Generated
│   │   ├── simple_detected.png     ✅ Visualization
│   │   ├── complex.png             ✅ Generated
│   │   └── office.png              ✅ Generated
│   └── download_samples.py
├── backend/
│   └── test_detection_local.py     ✅ Test script
└── frontend/
    └── (dev server running)        ✅ http://localhost:5173
```

---

**Time to first working detection: ~15 minutes** ⚡

Ready to test? Start with **Step 1** above!
