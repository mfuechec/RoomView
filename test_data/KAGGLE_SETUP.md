# 📥 Download CubiCasa5k Blueprints

## Quick Setup (2 minutes)

### Step 1: Get Your Kaggle API Token

1. **Go to Kaggle:** https://www.kaggle.com/settings
   - Sign in (or create a free account)

2. **Scroll down to "API" section**

3. **Click "Create New API Token"**
   - This downloads `kaggle.json` to your Downloads folder

### Step 2: Install the Token

The `kaggle.json` file should be in your Downloads folder. Move it to the right location:

```bash
# Move from Downloads to ~/.kaggle/
mv ~/Downloads/kaggle.json ~/.kaggle/

# Set correct permissions (required by Kaggle)
chmod 600 ~/.kaggle/kaggle.json
```

### Step 3: Download Blueprints

```bash
cd /Users/mfuechec/Desktop/GauntletProjects/RoomView/test_data
source ../backend/venv/bin/activate
python3 download_samples.py --num-samples 10
```

This will:
- Download 10 professional floor plan images from CubiCasa5k
- Save them to `blueprints/sample_01.png`, `sample_02.png`, etc.
- Copy them to `frontend/public/sample_blueprints/` for UI testing

---

## Alternative: Manual Download

If you don't want to use the API:

1. Go to: https://www.kaggle.com/datasets/emarva/cubicasa5k
2. Click "Download" (5 GB zip file)
3. Extract and manually copy 5-10 PNG files to `test_data/blueprints/`

---

## What You'll Get

**CubiCasa5k** contains:
- ✅ 5000 real architectural floor plans
- ✅ Professional CAD quality
- ✅ Variety of layouts (apartments, houses, offices)
- ✅ Multiple room types
- ✅ Perfect for testing RoomView detection

**File sizes:** Each blueprint is 1-5 MB

---

## After Download

Test detection on real blueprints:

```bash
cd ../backend
source venv/bin/activate

# Test on sample 1
python3 test_detection_local.py \
  --input ../test_data/blueprints/sample_01.png \
  --visualize

# Test on sample 2
python3 test_detection_local.py \
  --input ../test_data/blueprints/sample_02.png \
  --visualize
```

Then upload them via the UI at http://localhost:5173/

---

## Troubleshooting

**"401 Unauthorized" error:**
- Make sure `kaggle.json` is in `~/.kaggle/`
- Check permissions: `ls -la ~/.kaggle/kaggle.json` (should show `-rw-------`)

**"Dataset not found" error:**
- Verify the dataset URL: https://www.kaggle.com/datasets/emarva/cubicasa5k
- Make sure you're logged into Kaggle

**Download is slow:**
- The full dataset is 5 GB (we're only downloading small samples)
- Each sample is 1-5 MB
- 10 samples = ~30 MB total download
