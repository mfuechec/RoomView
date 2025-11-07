# RoomView Backend

AWS Lambda function for detecting room boundaries in architectural blueprints using OpenCV.

## Architecture

```
lambda_function.py          # Entry point
├── detection/
│   ├── preprocessing.py    # 7-stage image preprocessing pipeline
│   ├── opencv_detector.py  # Contour-based room detection
│   └── normalizer.py       # Coordinate normalization (0.0-1.0)
└── utils/
    ├── validation.py       # Image validation
    └── error_handling.py   # Error responses
```

## Setup

### Local Development

1. **Install Python 3.11+**
   ```bash
   python --version  # Should be 3.11+
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Tests**
   ```bash
   pytest tests/ -v --cov=detection --cov=utils
   ```

### AWS Deployment

1. **Create Lambda Layer for OpenCV**
   ```bash
   mkdir python
   pip install opencv-python-headless numpy pillow -t python/
   zip -r opencv-layer.zip python

   aws lambda publish-layer-version \
     --layer-name opencv-python311 \
     --zip-file fileb://opencv-layer.zip \
     --compatible-runtimes python3.11
   ```

2. **Package Lambda Function**
   ```bash
   zip -r deployment.zip lambda_function.py detection/ utils/
   ```

3. **Deploy to Lambda**
   ```bash
   aws lambda create-function \
     --function-name RoomViewDetector \
     --runtime python3.11 \
     --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role \
     --handler lambda_function.lambda_handler \
     --timeout 30 \
     --memory-size 2048 \
     --zip-file fileb://deployment.zip \
     --layers arn:aws:lambda:REGION:ACCOUNT_ID:layer:opencv-python311:1
   ```

4. **Update Function** (after changes)
   ```bash
   zip -r deployment.zip lambda_function.py detection/ utils/
   aws lambda update-function-code \
     --function-name RoomViewDetector \
     --zip-file fileb://deployment.zip
   ```

## Configuration

Environment variables (set in Lambda console or SAM template):

```yaml
MIN_ROOM_AREA: 1500          # Minimum room size in pixels
CONFIDENCE_THRESHOLD: 0.7     # Minimum confidence score
MAX_ROOMS: 50                 # Maximum rooms to return
LOG_LEVEL: INFO               # Logging level
```

## API Contract

### Request

```http
POST /detect
Content-Type: multipart/form-data

blueprint=<binary image data>
```

### Response (Success)

```json
{
  "status": "success",
  "blueprint_id": "bp_20251107_abc123",
  "processing_time_seconds": 18.42,
  "image_dimensions": {
    "width_pixels": 2400,
    "height_pixels": 1800
  },
  "total_rooms_detected": 8,
  "rooms": [
    {
      "id": "room_001",
      "bounding_box_normalized": [0.125, 0.083, 0.375, 0.533],
      "bounding_box_pixels": [300, 150, 900, 960],
      "confidence_score": 0.92,
      "type_hint": "room",
      "area_normalized": 0.1125,
      "area_pixels": 396000
    }
  ]
}
```

### Response (Error)

```json
{
  "status": "error",
  "error_code": "NO_ROOMS_FOUND",
  "message": "Unable to detect rooms in the uploaded image.",
  "suggestions": [
    "Ensure blueprint has clear wall lines",
    "Try a higher resolution scan"
  ]
}
```

## Error Codes

| Code | HTTP Status | Meaning |
|------|------------|---------|
| `INVALID_FORMAT` | 400 | Wrong file type |
| `FILE_TOO_LARGE` | 413 | > 10MB |
| `INVALID_IMAGE` | 422 | Corrupted file |
| `NO_ROOMS_FOUND` | 422 | Detection failed |
| `TIMEOUT` | 504 | > 30 seconds |
| `INTERNAL_ERROR` | 500 | Server issue |

## Testing

### Unit Tests

```bash
# Run all tests
pytest tests/

# With coverage
pytest tests/ --cov=detection --cov=utils --cov-report=html

# Run specific test file
pytest tests/test_preprocessing.py -v
```

### Integration Test (Local)

```python
# test_local.py
import base64
from lambda_function import lambda_handler

with open('sample_blueprint.png', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()

event = {
    'body': image_data,
    'isBase64Encoded': True,
    'headers': {'Content-Type': 'image/png'}
}

class MockContext:
    request_id = 'test-123'
    def get_remaining_time_in_millis(self):
        return 30000

response = lambda_handler(event, MockContext())
print(response)
```

## Performance

- **Preprocessing:** 2-5 seconds
- **Detection:** 15-20 seconds
- **Normalization:** < 1 second
- **Total:** < 30 seconds

## Troubleshooting

**Issue:** Lambda timeout
- Reduce `max_dimension` in preprocessing config (2000 → 1500)
- Increase Lambda memory (2048MB → 3008MB gives more CPU)

**Issue:** Poor detection accuracy
- Ensure blueprint has clear, dark wall lines
- Try different `canny_threshold` values
- Adjust `min_room_area_pixels` for blueprint scale

**Issue:** Too many false positives
- Increase `min_room_area_pixels`
- Increase `iou_threshold` for duplicate removal

## License

MIT
