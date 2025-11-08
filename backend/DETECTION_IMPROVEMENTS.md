# Room Detection Pipeline Improvements

## Problem Summary
**Original Accuracy:** ~1/10 rooms detected correctly
**Issue:** Clean but detailed blueprints triggered excessive false positives (furniture, fixtures, doors, etc.)

## Solution Overview
Created improved detection pipeline with **hierarchical contour analysis** and **better filtering** to eliminate false positives while preserving true rooms.

---

## Key Improvements

### 1. Hierarchical Contour Analysis (Most Important)
**Problem:** Original detector treated all contours equally
**Solution:** Uses parent-child relationships to identify true rooms

```python
# Old approach: Find any contour > min_size
contours = cv2.findContours(...)
rooms = [c for c in contours if cv2.contourArea(c) > min_area]

# New approach: Find enclosed spaces (rooms inside walls)
contours, hierarchy = cv2.findContours(...)  # Get hierarchy
rooms = find_rooms_with_parents(contours, hierarchy)
```

**How it works:**
- Rooms are "holes" (white spaces) enclosed by walls (black lines)
- Only keeps contours that have a parent contour
- Checks that room is 5-85% the size of its parent
- Eliminates furniture/fixtures that aren't properly enclosed

**File:** `backend/detection/opencv_detector_improved.py:91-141`

---

### 2. Better Size Filtering
**Changes:**
- `min_room_area_pixels`: 1500 → 5000 (more aggressive)
- Added `max_room_area_pixels`: 500000 (prevents detecting entire floor)
- Added `min_room_dimension`: 50px (width and height must exceed this)

**Rationale:** Rooms should be substantial. Furniture/fixtures are smaller.

**File:** `backend/detection/opencv_detector_improved.py:17-26`

---

### 3. Shape Quality Filters
Added multiple shape filters to eliminate irregular contours:

**Solidity** (contour_area / convex_hull_area):
- Rooms are solid shapes: solidity ≥ 0.6
- Furniture has irregular shapes: solidity < 0.6

**Extent** (contour_area / bounding_box_area):
- Rooms fill their bounding box: extent ≥ 0.5
- Irregular objects don't: extent < 0.5

**Aspect Ratio:**
- Min: 0.2 (reject very thin rectangles - doors/windows)
- Max: 8.0 (allow hallways)

**File:** `backend/detection/opencv_detector_improved.py:198-265`

---

### 4. Improved Morphological Operations
**Old:** Simple CLOSE operation (2 iterations)
**New:** Three-stage process:

1. **CLOSE** (kernel 3x3): Fill small gaps in walls
2. **OPEN** (kernel 5x5): **Remove small details/furniture**
3. **DILATE** (kernel 2x2): Strengthen wall lines

**Key Parameter:** `morph_open_size = 5`
- **Increase to 7-9** if still getting furniture/fixture false positives
- **Decrease to 3-4** if losing legitimate small rooms

**File:** `backend/detection/preprocessing_improved.py:91-148`

---

### 5. Better Confidence Scoring
**Old:** Simple rectangularity (area / bbox_area)
**New:** Weighted combination of 4 metrics:
- 30% Rectangularity
- 25% Solidity
- 25% Size appropriateness
- 20% Compactness

**File:** `backend/detection/opencv_detector_improved.py:268-304`

---

## Testing the Improvements

### Quick Test (Single Blueprint)

```bash
cd backend

# Run comparison on a single blueprint
python compare_detectors.py ../test_data/blueprint.png --display

# Save comparison image
python compare_detectors.py ../test_data/blueprint.png --output results.png

# Show preprocessing steps too
python compare_detectors.py ../test_data/blueprint.png --show-steps --output detailed.png
```

**Output:**
- Side-by-side comparison image
- Statistics showing: number of rooms, confidence scores
- Visual boxes drawn on blueprint

---

### Batch Test (Multiple Blueprints)

```bash
# Test on all blueprints in a folder
for file in ../test_data/*.png; do
    python compare_detectors.py "$file" --output "comparison_$(basename $file)"
done
```

---

## Tuning Parameters

### Configuration File: `backend/detection/config.py`

**For your use case (detailed CAD blueprints), try the `detailed_cad` preset:**

```python
# In your code
from detection.config import apply_preset

prep_config, det_config = apply_preset('detailed_cad')
```

**`detailed_cad` preset:**
- `morph_open_size`: 7 (aggressive detail removal)
- `min_room_area_pixels`: 8000 (larger minimum)
- `min_solidity`: 0.7 (stricter shapes)
- `min_area_ratio_to_parent`: 0.10

### Manual Tuning Guide

**Too many false positives (furniture/fixtures)?**
→ Increase `morph_open_size` (5 → 7 → 9)
→ Increase `min_room_area_pixels` (5000 → 8000 → 10000)
→ Increase `min_solidity` (0.6 → 0.7 → 0.8)

**Missing legitimate rooms?**
→ Decrease `min_room_area_pixels` (5000 → 3000)
→ Decrease `min_solidity` (0.6 → 0.5)
→ Decrease `morph_open_size` (5 → 3)

**Getting duplicate detections?**
→ Increase `iou_threshold` (0.5 → 0.6 → 0.7)

---

## Integration Options

### Option A: Replace Existing Detection (Recommended)

Update `backend/lambda_function.py`:

```python
# OLD:
from detection.preprocessing import preprocess_pipeline
from detection.opencv_detector import detect_rooms_opencv

# NEW:
from detection.preprocessing_improved import preprocess_pipeline_improved as preprocess_pipeline
from detection.opencv_detector_improved import detect_rooms_improved as detect_rooms_opencv

# Rest of code stays the same!
```

### Option B: A/B Testing Mode

Add environment variable to switch between pipelines:

```python
import os
USE_IMPROVED = os.environ.get('USE_IMPROVED_DETECTION', 'true').lower() == 'true'

if USE_IMPROVED:
    from detection.preprocessing_improved import preprocess_pipeline_improved as preprocess_pipeline
    from detection.opencv_detector_improved import detect_rooms_improved as detect_rooms_opencv
else:
    from detection.preprocessing import preprocess_pipeline
    from detection.opencv_detector import detect_rooms_opencv
```

### Option C: Keep Both (Local Testing Only)

Use comparison script for visual evaluation, then integrate winner.

---

## Expected Results

**Before (Original Pipeline):**
- ~1/10 accuracy
- Detects 50-100+ "rooms" (mostly false positives)
- Picks up furniture, doors, windows, fixtures
- Low confidence scores

**After (Improved Pipeline):**
- Expected: 6-8/10 accuracy (60-80%)
- Detects 5-15 rooms (mostly true positives)
- Filters out furniture/fixtures
- Higher confidence scores
- May still miss some rooms (human-in-the-loop handles this)

---

## Troubleshooting

### "Getting 0 rooms detected"
- Blueprints might be too clean/simple
- Try `clean_cad` preset instead of `detailed_cad`
- Decrease `min_room_area_pixels` to 3000
- Decrease `min_solidity` to 0.5

### "Still getting furniture as rooms"
- Increase `morph_open_size` to 7 or 9
- Increase `min_room_area_pixels` to 10000
- Increase `min_area_ratio_to_parent` to 0.15

### "Rooms look merged together"
- Decrease `morph_close_iterations` to 1 (or 0)
- Decrease `morph_dilate_size` to 1
- Check if walls in blueprint are actually disconnected

### "Processing takes too long"
- Decrease `max_dimension` from 2000 to 1500
- Decrease `denoise_strength` from 10 to 5
- Set `morph_open_iterations` to 1 (not higher)

---

## File Reference

**New Files Created:**
```
backend/
├── detection/
│   ├── opencv_detector_improved.py      # NEW: Improved detection with hierarchy
│   ├── preprocessing_improved.py        # NEW: Better morphological operations
│   └── config.py                        # NEW: Centralized configuration
└── compare_detectors.py                 # NEW: Visual comparison tool
```

**Existing Files (Unchanged):**
```
backend/
├── detection/
│   ├── opencv_detector.py              # Original (kept for comparison)
│   ├── preprocessing.py                # Original (kept for comparison)
│   └── normalizer.py                   # Still used (no changes needed)
├── lambda_function.py                  # Update imports here
└── test_detection_local.py             # Can update to use improved version
```

---

## Next Steps

1. **Test the comparison script:**
   ```bash
   cd backend
   python compare_detectors.py path/to/your/blueprint.png --display
   ```

2. **Review results visually** - Are false positives reduced?

3. **Tune parameters** in `detection/config.py` if needed

4. **Integrate** into lambda_function.py (Option A recommended)

5. **Deploy** and test with real blueprints

6. **Iterate** based on results (this is expected for CV projects)

---

## Architecture Decision

**Why hierarchical analysis?**
- Computer vision principle: Rooms are *enclosed spaces*
- Parent-child relationships naturally model this
- Industry standard for floor plan analysis
- Dramatically reduces false positives

**Why not machine learning?**
- MVP scope: OpenCV is faster to implement
- No training data required
- Deterministic and debuggable
- Can add ML layer later if needed

---

**Questions or issues?** Test with `compare_detectors.py` first, then tune config.py parameters.
