# RoomView - System Architecture Document

## Overview
**Project Name:** RoomView - AI-Powered Blueprint Room Detection
**Version:** v1.0
**Date:** November 2025
**Architect:** Winston (System Architect)
**Status:** Ready for Implementation

### Architecture Overview
RoomView is a serverless, event-driven system that uses computer vision to automatically detect room boundaries from architectural blueprint images. The architecture prioritizes simplicity, rapid development, and demo-readiness while maintaining clear paths for future production scaling.

**Core Design Principles:**
- **Serverless-First:** Zero infrastructure management, pay-per-use
- **Stateless Processing:** Each request is independent, simplifies scaling
- **Human-in-the-Loop:** AI provides suggestions, user has final control
- **Fail-Fast:** Clear error messages, graceful degradation

---

## System Architecture

**Architecture Style:** Serverless + Event-Driven (AWS Lambda)

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER LAYER                              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              React Single-Page Application              │    │
│  │  • Blueprint Upload Component                           │    │
│  │  • Canvas Renderer (Konva.js)                          │    │
│  │  • Room Editor (Drag/Resize/Delete)                    │    │
│  │  • State Management (React Context + LocalStorage)     │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            ↓ HTTPS
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                                │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              AWS API Gateway (REST API)                 │    │
│  │  • CORS Configuration                                   │    │
│  │  • Request Validation                                   │    │
│  │  • API Key Authentication (optional for MVP)            │    │
│  │  • Rate Limiting (100 req/min)                          │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            ↓ Invoke
┌─────────────────────────────────────────────────────────────────┐
│                      PROCESSING LAYER                            │
│  ┌────────────────────────────────────────────────────────┐    │
│  │          AWS Lambda: RoomDetectionHandler               │    │
│  │  Runtime: Python 3.11                                   │    │
│  │  Memory: 2048 MB                                        │    │
│  │  Timeout: 30 seconds                                    │    │
│  │                                                          │    │
│  │  Sub-Modules:                                           │    │
│  │  ├─ 1. Image Preprocessor                              │    │
│  │  ├─ 2. Detection Engine (OpenCV)                       │    │
│  │  └─ 3. Postprocessor & Response Builder                │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            ↓ Uses
┌─────────────────────────────────────────────────────────────────┐
│                       STORAGE LAYER (MVP)                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           Frontend LocalStorage Only                    │    │
│  │  • Original blueprint (base64)                          │    │
│  │  • Detected rooms JSON                                  │    │
│  │  • User corrections                                     │    │
│  │  • No server-side persistence                           │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

**Key Architectural Decisions:**
1. **Synchronous Processing:** 30-second timeout is acceptable for MVP, simplifies client logic
2. **No Database:** State lives in browser, reduces AWS costs and complexity
3. **Monolithic Lambda:** Single function handles all processing, avoids orchestration overhead
4. **OpenCV Over AWS AI:** More control, faster iteration, proven floor plan detection patterns

---

## Components

### 1. Frontend Application (React)

**Purpose:** User interface for blueprint upload, visualization, and manual editing

**Technology Stack:**
- React 18+ (Hooks-based)
- Vite (build tool)
- React-Konva (canvas rendering)
- Axios (HTTP client)

**Key Responsibilities:**
- File upload with validation (PNG/JPG/PDF, max 10MB)
- Render blueprint image as background layer
- Overlay detected room bounding boxes
- Enable drag-to-resize, click-to-delete interactions
- Export final JSON with corrections

**Component Tree:**
```
<App>
├── <Header> (logo, project name)
├── <BlueprintUploader>
│   ├── <FileInput> (drag-drop + file picker)
│   └── <UploadProgress> (loading spinner)
├── <BlueprintCanvas>
│   ├── <Stage> (Konva root)
│   ├── <Layer name="background">
│   │   └── <Image src={blueprint} />
│   ├── <Layer name="rooms">
│   │   └── {rooms.map(r => <RoomBoundingBox {...r} />)}
│   └── <Layer name="controls">
│       └── <Transformer> (resize handles)
├── <RoomList> (sidebar, shows detected rooms)
│   └── {rooms.map(r => <RoomListItem {...r} />)}
├── <Toolbar>
│   ├── <ExportButton> (download JSON)
│   ├── <AddRoomButton> (manual room creation)
│   └── <ResetButton> (clear all)
└── <ErrorBoundary> (catch React errors)
```

**State Management:**
```javascript
// React Context + useReducer
const AppState = {
  blueprint: { file: File, dataUrl: string, dimensions: {w, h} },
  detectedRooms: Room[], // Original AI output
  editedRooms: Room[],   // User modifications
  processingStatus: 'idle' | 'uploading' | 'processing' | 'complete' | 'error',
  error: string | null
}
```

**Interfaces:**
- `POST /api/v1/detect` - Upload blueprint, receive room coordinates
- LocalStorage persistence for state recovery

---

### 2. API Gateway

**Purpose:** HTTP endpoint for frontend-backend communication

**Technology:** AWS API Gateway (REST API)

**Configuration:**
```yaml
Resource: /detect
Method: POST
Authorization: API Key (optional for MVP)
CORS: Enabled (* for demo, restrict in production)
Request Validation: Enabled
  - Content-Type: multipart/form-data
  - Max payload: 10MB
Integration: Lambda Proxy
Throttling: 100 requests/minute
```

**Response Headers:**
```
Access-Control-Allow-Origin: *
Content-Type: application/json
X-Processing-Time: <milliseconds>
```

---

### 3. Lambda Function: RoomDetectionHandler

**Purpose:** Core detection logic using OpenCV computer vision

**Technology:**
- Python 3.11
- OpenCV (cv2) - Image processing
- NumPy - Numerical operations
- PIL/Pillow - Image format handling

**Configuration:**
```yaml
Function Name: RoomViewDetector
Runtime: python3.11
Memory: 2048 MB (OpenCV needs memory for image processing)
Timeout: 30 seconds
Environment Variables:
  - MIN_ROOM_AREA: 1500 (pixels)
  - CONFIDENCE_THRESHOLD: 0.7
  - MAX_ROOMS: 50
  - LOG_LEVEL: INFO
```

**Lambda Layer:**
- OpenCV + dependencies (~100MB)
- Pre-built layer: arn:aws:lambda:us-east-1:XXX:layer:opencv-python311

**Execution Flow:**
```python
def lambda_handler(event, context):
    try:
        # 1. PREPROCESSING (2-5 seconds)
        image = decode_image(event['body'])
        preprocessed = preprocess_pipeline(image)

        # 2. DETECTION (15-20 seconds)
        rooms = detect_rooms_opencv(preprocessed)

        # 3. POSTPROCESSING (2-3 seconds)
        normalized_rooms = normalize_coordinates(rooms, image.shape)
        response = build_response(normalized_rooms)

        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    except Exception as e:
        return handle_error(e)
```

---

## Technology Stack

### Frontend
```yaml
framework: React 18.2+
build_tool: Vite 5.x
state_management: React Context API + useReducer
canvas_library: react-konva 18.x
styling: CSS Modules + Tailwind CSS (optional)
http_client: Axios 1.x
file_handling: FileReader API (native)
key_libraries:
  - konva: Canvas manipulation
  - axios: HTTP requests
  - react-router-dom: Client-side routing (optional)
```

### Backend
```yaml
language: Python 3.11
runtime: AWS Lambda
api_framework: AWS API Gateway (managed)
key_libraries:
  - opencv-python: 4.8.x (computer vision)
  - numpy: 1.24.x (numerical operations)
  - pillow: 10.x (image format handling)
  - boto3: 1.28.x (AWS SDK, if using S3 later)
```

### Infrastructure
```yaml
cloud_platform: AWS
compute: Lambda (serverless)
api_gateway: AWS API Gateway (REST API)
storage: None (MVP), LocalStorage (client-side)
deployment: AWS SAM or Serverless Framework
ci_cd: GitHub Actions (optional for MVP)
monitoring: CloudWatch Logs + CloudWatch Metrics
```

---

## Image Preprocessing Pipeline

**Goal:** Transform raw blueprint images into clean, normalized format optimized for detection

### Pipeline Stages

```python
def preprocess_pipeline(raw_image: np.ndarray) -> dict:
    """
    Multi-stage preprocessing pipeline
    Estimated time: 2-5 seconds
    """

    # STAGE 1: Decode & Validate (0.5s)
    if raw_image is None:
        raise ValueError("Invalid image data")

    original_shape = raw_image.shape

    # STAGE 2: Resize (0.5s)
    # Normalize to max dimension 2000px for consistent processing
    resized = resize_maintain_aspect_ratio(
        raw_image,
        max_dimension=2000
    )

    # STAGE 3: Convert to Grayscale (0.2s)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    # STAGE 4: Noise Reduction (0.5s)
    denoised = cv2.fastNlMeansDenoising(
        gray,
        h=10,
        templateWindowSize=7,
        searchWindowSize=21
    )

    # STAGE 5: Contrast Enhancement (0.3s)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)

    # STAGE 6: Thresholding (0.2s)
    _, binary = cv2.threshold(
        enhanced,
        0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # STAGE 7: Morphological Operations (0.5s)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    return {
        'processed': closed,
        'original_shape': original_shape,
        'scale_factor': original_shape[0] / closed.shape[0]
    }
```

**Configuration Parameters:**
```python
PREPROCESSING_CONFIG = {
    'max_dimension': 2000,
    'denoise_strength': 10,
    'contrast_clip_limit': 2.0,
    'morph_iterations': 2,
    'min_file_size': 10_000,
    'max_file_size': 10_485_760
}
```

---

## Room Detection Algorithm

**Approach:** OpenCV-based contour detection using morphological analysis

### Detection Strategy

```python
def detect_rooms_opencv(preprocessed: dict) -> List[Room]:
    """
    Detect room boundaries using OpenCV contour detection
    Estimated time: 15-20 seconds
    """

    image = preprocessed['processed']

    # STEP 1: Edge Detection (2s)
    edges = cv2.Canny(image, threshold1=50, threshold2=150, apertureSize=3)

    # STEP 2: Find Contours (3s)
    contours, hierarchy = cv2.findContours(
        edges,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE
    )

    # STEP 3: Filter by Size (2s)
    min_area = 1500
    valid_contours = [c for c in contours if cv2.contourArea(c) > min_area]

    # STEP 4: Get Bounding Boxes (5s)
    rooms = []
    for idx, contour in enumerate(valid_contours):
        x, y, w, h = cv2.boundingRect(contour)

        area = cv2.contourArea(contour)
        bbox_area = w * h
        confidence = area / bbox_area

        aspect_ratio = max(w, h) / min(w, h)
        type_hint = 'hallway' if aspect_ratio > 4.0 else 'room'

        rooms.append({
            'id': f'room_{idx:03d}',
            'bounding_box': [x, y, x + w, y + h],
            'confidence_score': round(confidence, 2),
            'type_hint': type_hint,
            'area_pixels': int(area)
        })

    # STEP 5: Remove Duplicate/Overlapping Rooms (3s)
    rooms = remove_duplicates(rooms, iou_threshold=0.7)

    # STEP 6: Sort by area (largest first)
    rooms.sort(key=lambda r: r['area_pixels'], reverse=True)

    return rooms[:50]
```

---

## Coordinate Normalization Strategy

**Problem:** Blueprint images vary in resolution. Need consistent coordinate system.

**Solution:** Percentage-based normalization (0.0 to 1.0)

```python
def normalize_coordinates(rooms: List[Room], original_shape: tuple) -> List[Room]:
    """Convert pixel coordinates to normalized 0.0-1.0 range"""
    height, width = original_shape[:2]

    for room in rooms:
        x_min, y_min, x_max, y_max = room['bounding_box']

        room['bounding_box_normalized'] = [
            round(x_min / width, 4),
            round(y_min / height, 4),
            round(x_max / width, 4),
            round(y_max / height, 4)
        ]

        room['bounding_box_pixels'] = [x_min, y_min, x_max, y_max]

        norm_w = room['bounding_box_normalized'][2] - room['bounding_box_normalized'][0]
        norm_h = room['bounding_box_normalized'][3] - room['bounding_box_normalized'][1]
        room['area_normalized'] = round(norm_w * norm_h, 6)

    return rooms
```

### Frontend Rendering

```javascript
function denormalizeCoords(normalizedBox, canvasWidth, canvasHeight) {
  const [x_min_norm, y_min_norm, x_max_norm, y_max_norm] = normalizedBox;

  return {
    x: x_min_norm * canvasWidth,
    y: y_min_norm * canvasHeight,
    width: (x_max_norm - x_min_norm) * canvasWidth,
    height: (y_max_norm - y_min_norm) * canvasHeight
  };
}
```

---

## API Design

### Endpoint: POST /api/v1/detect

**Purpose:** Upload blueprint image and receive detected room coordinates

#### Request

```http
POST /api/v1/detect HTTP/1.1
Host: api.roomview.demo
Content-Type: multipart/form-data

--boundary
Content-Disposition: form-data; name="blueprint"; filename="floor_plan.png"
Content-Type: image/png

<binary image data>
--boundary--
```

**Request Validation:**
- File size: 10 KB - 10 MB
- Content-Type: `image/png`, `image/jpeg`, or `application/pdf`
- Field name must be `blueprint`

#### Response: Success (200 OK)

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

#### Response: Client Error (4xx)

**400 Bad Request**
```json
{
  "status": "error",
  "error_code": "INVALID_FORMAT",
  "message": "Unsupported file format. Please upload PNG, JPG, or PDF.",
  "details": "File type detected: application/zip"
}
```

**413 Payload Too Large**
```json
{
  "status": "error",
  "error_code": "FILE_TOO_LARGE",
  "message": "Image exceeds 10MB limit.",
  "details": "Uploaded file size: 12.3 MB"
}
```

**422 Unprocessable Entity**
```json
{
  "status": "error",
  "error_code": "PROCESSING_FAILED",
  "message": "Unable to detect rooms in the uploaded image.",
  "details": "No valid contours found.",
  "suggestions": [
    "Try a higher resolution scan",
    "Ensure blueprint has clear wall lines"
  ]
}
```

#### Response: Server Error (5xx)

**500 Internal Server Error**
```json
{
  "status": "error",
  "error_code": "INTERNAL_ERROR",
  "message": "An unexpected error occurred during processing.",
  "request_id": "req_abc123xyz"
}
```

**504 Gateway Timeout**
```json
{
  "status": "error",
  "error_code": "TIMEOUT",
  "message": "Processing exceeded 30-second limit.",
  "suggestions": [
    "Try a lower resolution image",
    "Crop blueprint to smaller sections"
  ]
}
```

### Error Code Reference

| Code | HTTP Status | Meaning | User Action |
|------|------------|---------|-------------|
| `INVALID_FORMAT` | 400 | Wrong file type | Upload PNG/JPG/PDF |
| `FILE_TOO_LARGE` | 413 | > 10MB | Compress image |
| `INVALID_IMAGE` | 422 | Corrupted file | Re-upload |
| `NO_ROOMS_FOUND` | 422 | Detection failed | Check image quality |
| `PROCESSING_FAILED` | 422 | Algorithm error | Try different blueprint |
| `TIMEOUT` | 504 | > 30 seconds | Reduce image size |
| `INTERNAL_ERROR` | 500 | Server issue | Retry later |

---

## State Management Strategy

**Problem:** PRD requires "both original and manually corrected data" but specifies "no database"

**Solution:** Client-side state management with LocalStorage persistence

### State Architecture

```javascript
const AppState = {
  blueprint: {
    file: File | null,
    dataUrl: string | null,
    fileName: string,
    dimensions: { width: number, height: number },
    uploadedAt: string
  },
  detectedRooms: Room[],    // Original AI output
  editedRooms: Room[],      // User modifications
  processingStatus: 'idle' | 'uploading' | 'processing' | 'complete' | 'error',
  selectedRoomId: string | null,
  error: ErrorState | null,
  sessionId: string,
  lastSaved: string
};

interface Room {
  id: string;
  bounding_box_normalized: [number, number, number, number];
  confidence_score?: number;
  type_hint?: 'room' | 'hallway' | 'unknown';
  isUserCreated?: boolean;
  isModified?: boolean;
  isDeleted?: boolean;
}
```

### State Persistence

```javascript
function persistState(state) {
  try {
    const serialized = JSON.stringify({
      blueprint: {
        fileName: state.blueprint.fileName,
        dataUrl: state.blueprint.dataUrl,
        dimensions: state.blueprint.dimensions
      },
      detectedRooms: state.detectedRooms,
      editedRooms: state.editedRooms,
      sessionId: state.sessionId,
      lastSaved: new Date().toISOString()
    });

    localStorage.setItem('roomview_session', serialized);
  } catch (e) {
    console.error('Failed to save state:', e);
  }
}

function restoreState() {
  const saved = localStorage.getItem('roomview_session');
  if (saved) {
    return JSON.parse(saved);
  }
  return null;
}
```

### Export Functionality

```javascript
function exportData(state) {
  const exportData = {
    export_version: '1.0',
    exported_at: new Date().toISOString(),
    blueprint: {
      file_name: state.blueprint.fileName,
      dimensions: state.blueprint.dimensions
    },
    detection_results: {
      original: state.detectedRooms,
      edited: state.editedRooms,
      summary: {
        rooms_detected: state.detectedRooms.length,
        rooms_after_editing: state.editedRooms.filter(r => !r.isDeleted).length,
        user_added: state.editedRooms.filter(r => r.isUserCreated).length,
        user_modified: state.editedRooms.filter(r => r.isModified).length,
        user_deleted: state.editedRooms.filter(r => r.isDeleted).length
      }
    }
  };

  const blob = new Blob([JSON.stringify(exportData, null, 2)], {
    type: 'application/json'
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `roomview_${state.sessionId}_${Date.now()}.json`;
  link.click();
}
```

---

## Error Handling & Retry Logic

### Client-Side Validation

```javascript
function validateBlueprint(file) {
  const errors = [];

  const validTypes = ['image/png', 'image/jpeg', 'application/pdf'];
  if (!validTypes.includes(file.type)) {
    errors.push({
      code: 'INVALID_TYPE',
      message: 'Please upload PNG, JPG, or PDF files only',
      severity: 'error'
    });
  }

  const maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    errors.push({
      code: 'FILE_TOO_LARGE',
      message: `File size exceeds 10MB limit`,
      severity: 'error'
    });
  }

  return errors;
}
```

### Network Retry with Exponential Backoff

```javascript
async function uploadWithRetry(file, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await uploadBlueprint(file);
      return response;
    } catch (error) {
      if (error.response?.status >= 400 && error.response?.status < 500) {
        throw error;  // Don't retry client errors
      }

      if (attempt === maxRetries) {
        throw new Error(`Upload failed after ${maxRetries} attempts`);
      }

      const delay = Math.pow(2, attempt - 1) * 1000;
      await sleep(delay);
    }
  }
}
```

### Lambda Error Handling

```python
def lambda_handler(event, context):
    try:
        result = process_blueprint(event)
        return success_response(result)

    except ImageValidationError as e:
        return error_response(422, 'INVALID_IMAGE', str(e))

    except DetectionFailedError as e:
        return error_response(422, 'NO_ROOMS_FOUND', str(e),
            suggestions=["Ensure blueprint has clear wall lines"])

    except TimeoutError as e:
        return error_response(504, 'TIMEOUT',
            "Processing exceeded time limit")

    except Exception as e:
        logger.exception("Unexpected error")
        return error_response(500, 'INTERNAL_ERROR',
            "An unexpected error occurred",
            request_id=context.request_id)
```

---

## Testing Strategy

### Testing Pyramid

```
         /\
        /  \  E2E Tests (5%)
       /----\  Integration Tests (25%)
      /      \ Unit Tests (70%)
     /--------\
```

### Unit Tests (Python)

```python
# tests/test_preprocessing.py
def test_resize_maintains_aspect_ratio():
    image = np.random.randint(0, 255, (2000, 4000, 3), dtype=np.uint8)
    result = preprocess_pipeline(image)
    assert result['processed'].shape[0] <= 2000

def test_coordinate_normalization():
    rooms = [{'id': 'r1', 'bounding_box': [100, 50, 300, 200]}]
    original_shape = (400, 600)
    normalized = normalize_coordinates(rooms, original_shape)
    assert normalized[0]['bounding_box_normalized'][0] == 100/600
```

### Integration Tests

```python
def test_end_to_end_detection():
    with open('tests/fixtures/sample_blueprint.png', 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()

    event = {'body': image_data, 'headers': {'Content-Type': 'image/png'}}
    response = lambda_handler(event, MockContext())

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['total_rooms_detected'] > 0
```

### E2E Tests (Cypress)

```javascript
describe('Room Detection Flow', () => {
  it('detects rooms in uploaded blueprint', () => {
    cy.visit('/');
    cy.get('[data-testid="file-input"]').selectFile('fixtures/sample.png');
    cy.get('[data-testid="room-box"]', { timeout: 35000 })
      .should('have.length.at.least', 1);
  });
});
```

---

## Deployment Architecture

### AWS Infrastructure

```yaml
Resources:
  RoomViewAPI:
    Type: AWS::ApiGatewayV2::Api
    Properties:
      Name: RoomView-API
      ProtocolType: HTTP
      CorsConfiguration:
        AllowOrigins: ['*']
        AllowMethods: ['POST', 'OPTIONS']

  RoomDetectionFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: RoomViewDetector
      Runtime: python3.11
      Handler: lambda_function.lambda_handler
      Timeout: 30
      MemorySize: 2048
      Environment:
        Variables:
          MIN_ROOM_AREA: 1500
          LOG_LEVEL: INFO
```

### Deployment Environments

| Environment | Purpose | Config |
|-------------|---------|--------|
| **Local Dev** | Development | Mock API |
| **AWS Demo** | Bootcamp | Full Lambda (2048MB) |

---

## Folder Structure

### Backend
```
roomview-backend/
├── lambda_function.py
├── detection/
│   ├── preprocessing.py
│   ├── opencv_detector.py
│   └── normalizer.py
├── utils/
│   ├── validation.py
│   └── error_handling.py
├── tests/
│   ├── test_preprocessing.py
│   └── test_detection.py
├── requirements.txt
└── template.yaml
```

### Frontend
```
roomview-frontend/
├── src/
│   ├── components/
│   │   ├── BlueprintUploader.jsx
│   │   ├── BlueprintCanvas.jsx
│   │   └── RoomList.jsx
│   ├── hooks/
│   │   └── useAppState.js
│   ├── services/
│   │   └── api.js
│   └── App.jsx
├── package.json
└── vite.config.js
```

---

## Decision Log

**Decision 1: OpenCV over AWS Textract**
- **Rationale:** More control, proven floor plan detection, free
- **Trade-offs:** More code to write

**Decision 2: Synchronous API**
- **Rationale:** Simpler client logic, 30s acceptable for demo
- **Trade-offs:** Long HTTP connection

**Decision 3: LocalStorage over Database**
- **Rationale:** Zero backend persistence, fast, sufficient for demo
- **Trade-offs:** Data lost if browser cleared

**Decision 4: Percentage-based Coordinates (0.0-1.0)**
- **Rationale:** Standard, flexible, resolution-independent
- **Trade-offs:** None

**Decision 5: Monolithic Lambda**
- **Rationale:** Simpler deployment, no orchestration
- **Trade-offs:** Harder to scale stages independently

---

## Next Steps

### Immediate Actions

1. **Review & Approve Architecture**
2. **Set Up Development Environment**
   - AWS account with Lambda/API Gateway
   - Python 3.11 + OpenCV
   - React + Vite
3. **Create Test Data**
   - Download 5 sample blueprints
4. **Proof of Concept**
   - Standalone Python script to test OpenCV detection

### Weekend Sprint

**Saturday (8h):** Backend implementation
**Sunday AM (6h):** Frontend development
**Sunday PM (4h):** Testing, demo prep

---

**Document Status:** Complete & Ready for Implementation
**Last Updated:** November 2025
