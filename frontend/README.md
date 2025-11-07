# RoomView Frontend

React application for visualizing and editing AI-detected room boundaries from architectural blueprints.

## Features

- 📤 Drag-and-drop blueprint upload
- 🎨 Interactive canvas with room overlays
- ✏️ Manual room editing (delete detected rooms)
- 📊 Real-time detection results
- 💾 Export results as JSON
- 💿 LocalStorage persistence (survives page refresh)

## Architecture

```
src/
├── components/          # React components
│   ├── Header.jsx
│   ├── BlueprintUploader.jsx
│   ├── BlueprintCanvas.jsx
│   ├── RoomList.jsx
│   ├── Toolbar.jsx
│   └── ErrorDisplay.jsx
├── hooks/
│   └── useAppState.jsx  # Global state management (Context + useReducer)
├── services/
│   └── api.js           # API client with retry logic
├── utils/
│   ├── validation.js    # File validation
│   └── coordinates.js   # Coordinate conversion
├── App.jsx
└── main.jsx
```

## Setup

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
# Start dev server
npm run dev

# Open http://localhost:5173
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

```env
# Point to your Lambda API Gateway endpoint
VITE_API_URL=https://your-api-gateway-url.amazonaws.com/prod
```

### Build for Production

```bash
npm run build

# Output: dist/
```

### Testing

```bash
# Run tests
npm test

# Run tests with UI
npm run test:ui
```

## Usage

1. **Upload Blueprint**: Drag & drop or click to select a PNG/JPG/PDF file (max 10MB)
2. **View Detected Rooms**: Rooms appear as colored bounding boxes on the canvas
3. **Edit Results**: Click rooms in the sidebar to select, click × to delete
4. **Export**: Click "Export JSON" to download results with both original and edited data

## State Management

Uses React Context + useReducer for global state:

```javascript
{
  blueprint: { file, dataUrl, fileName, dimensions },
  detectedRooms: [],      // Original AI output (immutable)
  editedRooms: [],        // User modifications (mutable)
  processingStatus: 'idle' | 'uploading' | 'processing' | 'complete' | 'error',
  error: { code, message, suggestions },
  sessionId: 'uuid',
  lastSaved: 'timestamp'
}
```

State automatically persists to `localStorage` for recovery after page refresh.

## API Integration

### Endpoint

```
POST /detect
Content-Type: multipart/form-data

blueprint=<file>
```

### Response

```json
{
  "status": "success",
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

### Mock API

For development without backend:

```javascript
import { mockUploadBlueprint } from './services/api'

// Use mock instead of real API
const result = await mockUploadBlueprint(file)
```

## Deployment

### Option 1: Vercel

```bash
npm install -g vercel
vercel
```

### Option 2: Netlify

```bash
npm install -g netlify-cli
netlify deploy --prod
```

### Option 3: AWS S3 + CloudFront

```bash
npm run build
aws s3 sync dist/ s3://your-bucket-name
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

## Troubleshooting

**Issue:** CORS errors when calling API
- Ensure API Gateway has CORS enabled
- Check `Access-Control-Allow-Origin` header

**Issue:** "Network Error" when uploading
- Check `VITE_API_URL` in `.env`
- Verify backend is running
- Try mock API for local testing

**Issue:** State lost after refresh
- Check browser's LocalStorage isn't full
- Verify no privacy extensions blocking storage

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## License

MIT
