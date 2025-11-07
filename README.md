# RoomView - AI-Powered Blueprint Room Detection

Automatically detect and extract room boundaries from architectural blueprint images using computer vision, reducing a 10-room floor plan setup from 5 minutes to under 30 seconds.

## Overview

RoomView is a serverless AI service that uses OpenCV-based computer vision to automatically detect room boundaries in architectural blueprints. This weekend MVP demonstrates the feasibility of automating tedious manual tracing tasks.

### Key Features

- **Automatic Detection**: Upload a blueprint, get room bounding boxes in < 30 seconds
- **Human-in-the-Loop**: Manually adjust, delete, or add rooms as needed
- **Export Results**: Download JSON with both original and corrected room data
- **Demo-Ready**: Polished UI, error handling, and sample blueprints included

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│   React     │  HTTPS  │ API Gateway  │ Invoke  │AWS Lambda    │
│   Frontend  │────────▶│   (REST)     │────────▶│(Python 3.11) │
│   (Vite)    │◀────────│              │◀────────│+ OpenCV      │
└─────────────┘         └──────────────┘         └──────────────┘
      │                                                  │
      │ LocalStorage                                    │
      ▼                                                  ▼
  User State                                      CloudWatch Logs
```

### Tech Stack

**Frontend:**
- React 18 + Vite
- Canvas API for blueprint rendering
- LocalStorage for state persistence

**Backend:**
- AWS Lambda (Python 3.11)
- OpenCV for room detection
- API Gateway for REST endpoint

**Detection Algorithm:**
- 7-stage preprocessing pipeline (resize, grayscale, denoise, enhance, threshold, morphology)
- Contour-based detection with size filtering
- Duplicate removal using IoU (Intersection over Union)
- Coordinate normalization (percentage-based)

## Project Structure

```
RoomView/
├── docs/
│   ├── prd.md                    # Product Requirements Document
│   └── architecture.md           # System Architecture (complete)
├── backend/                      # AWS Lambda function
│   ├── lambda_function.py        # Entry point
│   ├── detection/
│   │   ├── preprocessing.py      # Image preprocessing
│   │   ├── opencv_detector.py    # Room detection
│   │   └── normalizer.py         # Coordinate normalization
│   ├── utils/
│   │   ├── validation.py         # Input validation
│   │   └── error_handling.py     # Error responses
│   ├── requirements.txt
│   ├── template.yaml             # AWS SAM template
│   └── README.md
└── frontend/                     # React application
    ├── src/
    │   ├── components/           # React components
    │   ├── hooks/                # State management
    │   ├── services/             # API client
    │   └── utils/                # Validation & coordinates
    ├── package.json
    ├── vite.config.js
    └── README.md
```

## Quick Start

### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Test locally (requires sample blueprint)
python -m pytest tests/

# Deploy to AWS (requires AWS CLI configured)
sam build
sam deploy --guided
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure API endpoint
cp .env.example .env
# Edit .env: VITE_API_URL=<your-api-gateway-url>

# Start dev server
npm run dev

# Open http://localhost:5173
```

## Usage

1. **Upload Blueprint**: Drag & drop or select a PNG/JPG/PDF file (max 10MB)
2. **Processing**: Wait up to 30 seconds for detection to complete
3. **Review Results**: View detected rooms as colored bounding boxes
4. **Edit**: Click rooms to select, × to delete
5. **Export**: Download JSON with room coordinates

## API Reference

### POST /detect

Upload blueprint and receive detected rooms.

**Request:**
```http
POST /detect
Content-Type: multipart/form-data

blueprint=<file>
```

**Response (200 OK):**
```json
{
  "status": "success",
  "processing_time_seconds": 18.42,
  "total_rooms_detected": 8,
  "rooms": [
    {
      "id": "room_001",
      "bounding_box_normalized": [0.125, 0.083, 0.375, 0.533],
      "confidence_score": 0.92,
      "type_hint": "room"
    }
  ]
}
```

**Error Codes:**
- `400 INVALID_FORMAT` - Wrong file type
- `413 FILE_TOO_LARGE` - Exceeds 10MB
- `422 NO_ROOMS_FOUND` - Detection failed
- `504 TIMEOUT` - Processing > 30s

## Development

### Running Tests

**Backend:**
```bash
cd backend
pytest tests/ -v --cov=detection
```

**Frontend:**
```bash
cd frontend
npm test
```

### Mock API (No Backend Required)

```javascript
// In frontend/src/services/api.js
import { mockUploadBlueprint } from './services/api'

// Returns mock detection results after 2s delay
const result = await mockUploadBlueprint(file)
```

## Deployment

### Backend (AWS)

```bash
cd backend

# Build and deploy using SAM
sam build
sam deploy --stack-name roomview --capabilities CAPABILITY_IAM

# Get API endpoint
aws cloudformation describe-stacks --stack-name roomview \
  --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
  --output text
```

### Frontend (Vercel)

```bash
cd frontend
npm install -g vercel
vercel --prod
```

Or use Netlify, AWS S3 + CloudFront, or any static hosting.

## Weekend Sprint Timeline

- **Day 1 (Saturday):** Backend - Preprocessing, detection, Lambda setup (8 hours)
- **Day 2 (Sunday AM):** Frontend - React UI, canvas rendering (6 hours)
- **Day 2 (Sunday PM):** Integration testing, demo prep (4 hours)

## Performance

- **Preprocessing:** 2-5 seconds
- **Detection:** 15-20 seconds
- **Total:** < 30 seconds (Lambda timeout)

## Limitations (MVP)

- Clean CAD blueprints only (hand-drawn not supported)
- Bounding boxes (not precise polygons)
- Single blueprint at a time
- No server-side persistence (LocalStorage only)
- 80% detection accuracy target (human-in-the-loop required)

## Future Enhancements

- Curved wall detection
- Multi-floor blueprints
- Batch processing
- S3 storage + user accounts
- Integration with existing room naming AI
- Mobile app support

## Documentation

- **[PRD](docs/prd.md)** - Product requirements, success metrics, timeline
- **[Architecture](docs/architecture.md)** - Complete system design with diagrams
- **[Backend README](backend/README.md)** - Lambda deployment guide
- **[Frontend README](frontend/README.md)** - React app documentation

## Troubleshooting

**Lambda timeout:**
- Reduce `max_dimension` in preprocessing (2000 → 1500)
- Increase Lambda memory (more CPU)

**Poor accuracy:**
- Ensure blueprint has clear wall lines
- Try different `canny_threshold` values
- Adjust `min_room_area_pixels`

**CORS errors:**
- Verify API Gateway CORS settings
- Check `Access-Control-Allow-Origin: *`

## License

MIT

## Credits

Built as a weekend MVP bootcamp project demonstrating:
- Serverless architecture best practices
- Computer vision for document processing
- Human-in-the-loop AI workflows
- Rapid prototyping for customer validation

---

**Status:** ✅ Ready for Development
**Next Steps:** Review architecture docs → Set up dev environment → Start backend implementation
