# Product Requirements Document: Location Detection AI

## Executive Summary

**Project Name:** RoomView - AI-Powered Blueprint Room Detection
**Version:** v1.0 (Weekend MVP)
**Date:** November 2025
**Status:** Draft
**Timeline:** Weekend Sprint (2-3 days)
**Context:** Bootcamp demo project designed to be customer-ready with minimal changes

### Overview
RoomView is an AI service that automatically detects and extracts room boundaries from architectural blueprint images, eliminating the tedious manual tracing process. This tool will reduce a 10-room floor plan setup from 5 minutes to under 30 seconds, serving as a major competitive differentiator for the Innergy platform.

---

## 1. Problem Statement

### The Problem
Users currently waste 5+ minutes manually tracing room boundaries on architectural blueprints using 2D CAD tools. For a typical 10-room floor plan, this involves:
- Opening the blueprint
- Selecting drawing tools
- Clicking dozens of points to trace each room's walls
- Verifying accuracy
- Repeating for every single room and hallway

This manual process is tedious, error-prone, and scales poorly as building complexity increases.

### User Pain Points
- **Time-consuming:** 30-60 seconds per room × 10+ rooms = significant overhead
- **Tedious clicking:** Each room requires precise mouse clicks around boundaries
- **Error-prone:** Easy to miss corners or misalign boundaries
- **Repetitive work:** Same boring task for every blueprint
- **Blocks value delivery:** Users want to work with room data, not create it

### Current State
Innergy already has an internal AI tool that successfully extracts room names and numbers AFTER users manually draw boundaries. The missing piece is automating the boundary-drawing step itself.

---

## 2. Goals & Success Metrics

### Primary Goal
Reduce manual room boundary definition time from 5 minutes to under 30 seconds for a typical 10-room floor plan through AI-powered automatic detection.

### Success Metrics

| Metric | Target (MVP) | Measurement Method |
|--------|--------------|-------------------|
| **Processing Time** | < 30 seconds per blueprint | Backend service latency monitoring |
| **Detection Accuracy** | ≥ 80% of rooms detected correctly | Manual validation on test blueprints |
| **Time Savings** | 90% reduction in setup time | Before/after user timing studies |
| **False Positive Rate** | < 10% | Count of incorrectly detected "rooms" |
| **Demo Success** | Impressively handles 3+ sample blueprints | Qualitative assessment |

### Definition of Success for Weekend MVP
- Service processes clean blueprints and returns bounding boxes
- React UI displays detected rooms overlaid on blueprint
- Human-in-the-loop: Users can manually adjust incorrect detections
- Demo-ready: Looks polished enough for customer presentation

---

## 3. Definitions & Terminology

### What is a "Room"?
For the purposes of this MVP, a **room** is defined as:

**IN SCOPE (Detect These):**
- Enclosed spaces with 3+ walls (bedrooms, offices, kitchens, bathrooms)
- Hallways and corridors
- Open-plan areas with clear boundary markers
- Rectangular or irregular polygon shapes

**OUT OF SCOPE (Do NOT Detect):**
- Closets and small storage spaces (< 15 sq ft)
- Outdoor spaces (patios, balconies, parking)
- Stairwells and elevator shafts (future phase)
- Mezzanines and split-level spaces (treat as separate rooms if detected)

### Boundary Definition
- **Bounding Box:** The smallest rectangle that fully contains a room (x_min, y_min, x_max, y_max)
- **Normalized Coordinates:** All coordinates expressed in 0-1000 range for consistency
- **Wall:** A line segment representing a physical barrier between spaces

---

## 4. Target Users

### Primary User Persona: "Busy Building Manager"
- **Role:** Facility manager, building operator, or real estate professional
- **Needs:**
  - Fast blueprint digitization
  - Minimal technical expertise required
  - Accurate room data for space planning
- **Behaviors:**
  - Uploads 5-20 blueprints per week
  - Values time savings over pixel-perfect accuracy
  - Willing to make minor manual corrections
  - Needs results quickly (same session)

### Secondary User: "Innergy Sales Team"
- **Needs:** Impressive demo feature to differentiate product
- **Behaviors:** Shows tool to prospects, emphasizes time savings

---

## 5. Proposed Solution

### System Architecture (High-Level)

```
User (React App)
    ↓ [Upload Blueprint Image]
AWS API Gateway
    ↓
Lambda Function (Preprocessing)
    ↓
AWS AI/ML Service (Detection Logic)
    ↓
Lambda Function (Postprocessing)
    ↓ [Return JSON with Room Coordinates]
React App (Render Detected Rooms)
```

### Core Functional Requirements

**MUST HAVE (MVP):**
1. Accept blueprint images (PNG, JPG, PDF)
2. Process clean, professional blueprints
3. Detect rooms and hallways (rectangular and irregular)
4. Return JSON with bounding box coordinates for each room
5. Process within 30 seconds
6. Handle blueprints with 5-20 rooms
7. Provide UI to display detected boundaries overlaid on blueprint
8. Allow manual correction/adjustment of boundaries (human-in-the-loop)

**SHOULD HAVE (If Time Permits):**
- Basic confidence scores for each detection
- Simple room type classification hint ("bedroom", "hallway", etc.)
- Batch processing for multiple blueprints

**WON'T HAVE (Future Phases):**
- Custom model training
- Curved wall detection
- 3D floor plan support
- Real-time collaborative editing
- Integration with existing Innergy room naming AI (future phase)

---

## 6. Technical Requirements

### Tech Stack

**Frontend:**
- React (existing Innergy stack)
- Blueprint rendering library (React-Konva or Canvas API)
- File upload component

**Backend/Infrastructure:**
- **Cloud Platform:** AWS (mandatory)
- **Compute:** AWS Lambda (serverless)
- **API:** AWS API Gateway
- **AI/ML Services:**
  - Amazon Textract (document/line extraction)
  - Amazon Rekognition Custom Labels (if custom training needed)
  - OR Amazon SageMaker (pre-trained CV models)
  - Consider: Open-source CV libraries (OpenCV) if AWS services insufficient

**Development Tools:**
- Visual Studio Code
- Git/GitHub
- AWS CLI
- Postman (API testing)

### Performance Requirements

| Requirement | Target | Priority |
|-------------|--------|----------|
| **Latency** | < 30 seconds per blueprint | P0 (Must Have) |
| **Accuracy** | ≥ 80% room detection rate | P0 (Must Have) |
| **Throughput** | 1 blueprint at a time (no concurrency needed for MVP) | P1 (Should Have) |
| **Availability** | 95%+ uptime (demo context) | P2 (Nice to Have) |
| **Cost** | Stay within AWS free tier | P0 (Must Have) |

### Non-Functional Requirements

**Security:**
- No PII or sensitive data in blueprints (mock data for demo)
- HTTPS for all API calls
- Basic API key authentication

**Scalability:**
- Single-user demo (no horizontal scaling needed for MVP)
- Architecture should support multi-user expansion

**Usability:**
- Upload-to-result in < 60 seconds total (including UI interaction)
- Clear error messages if processing fails
- Visual feedback during processing (loading spinner)

### Constraints & Off-Limits

✅ **Allowed:**
- AWS AI/ML services
- Established engineering principles
- Open-source computer vision libraries
- Pre-trained models

❌ **Forbidden:**
- "Magic" or handwavy solutions
- Proprietary Innergy blueprints (use public domain samples)
- Overspending AWS credits
- Solutions requiring weeks of custom training

---

## 7. Scope & Boundaries

### In Scope (MVP - This Weekend)
1. Single blueprint upload and processing
2. Room and hallway detection (bounding boxes)
3. Clean, professional blueprint images
4. JSON output with normalized coordinates
5. React UI to display results
6. Basic manual correction capability
7. 3-5 sample blueprints for demo
8. AWS serverless deployment
9. Basic error handling

### Out of Scope (Future Phases)
1. Closet/storage detection
2. Curved wall support
3. 3D/multi-floor blueprints
4. Real-time collaborative editing
5. Integration with Innergy production system
6. Custom ML model training
7. Mobile app support
8. Batch processing UI
9. Advanced room type classification
10. Automated room naming (exists separately)

### Edge Cases & Handling Strategy

| Edge Case | MVP Approach | Future Enhancement |
|-----------|--------------|-------------------|
| **Irregular room shapes** | Detect with best-effort bounding box | Precise polygon boundaries |
| **Curved walls** | Approximate as straight lines | Curve detection |
| **Open-plan spaces** | Detect as single large room | Split based on furniture/fixtures |
| **Overlapping spaces** | Choose largest detection | Handle both with confidence scores |
| **Low-quality scans** | Fail gracefully with error message | Preprocessing to enhance quality |
| **Hand-drawn blueprints** | Out of scope | Support in future |
| **Split-level/mezzanine** | Treat as two separate rooms if detected | Special handling |

---

## 8. User Stories & Acceptance Criteria

### Epic: Automatic Room Detection

**User Story 1: Blueprint Upload**
- **As a** building manager
- **I want to** upload a blueprint image to the system
- **So that** I can automatically detect room boundaries without manual tracing

**Acceptance Criteria:**
- [ ] User can select a file from their computer (PNG, JPG, or PDF)
- [ ] File uploads successfully to AWS
- [ ] User sees confirmation that upload succeeded
- [ ] System validates file type and size (< 10MB)
- [ ] Clear error message if upload fails

---

**User Story 2: Room Detection Processing**
- **As a** building manager
- **I want to** see detected room boundaries on my blueprint
- **So that** I can verify the AI correctly identified all rooms

**Acceptance Criteria:**
- [ ] Processing completes in < 30 seconds
- [ ] User sees loading indicator during processing
- [ ] Detected rooms displayed as colored bounding boxes overlaid on blueprint
- [ ] Each room has a unique ID
- [ ] At least 80% of actual rooms are detected
- [ ] False positive rate < 10%

---

**User Story 3: Manual Correction**
- **As a** building manager
- **I want to** manually adjust incorrect room boundaries
- **So that** I can fix any AI detection errors

**Acceptance Criteria:**
- [ ] User can click and drag to resize bounding boxes
- [ ] User can delete false positive detections
- [ ] User can manually add missed rooms
- [ ] Changes persist in the UI
- [ ] Corrections can be saved/exported

---

**User Story 4: Export Results**
- **As a** building manager
- **I want to** export the detected room data
- **So that** I can use it in other systems

**Acceptance Criteria:**
- [ ] User can download JSON with room coordinates
- [ ] JSON follows the defined schema (see Section 9)
- [ ] Coordinates are normalized (0-1000 range)
- [ ] Export includes both original and manually corrected data

---

## 9. Data Models & Schemas

### Input: Blueprint Image
**Format:** PNG, JPG, or PDF
**Max Size:** 10MB
**Requirements:** Clean, professional architectural blueprint

**Mock Input Data Structure** (for testing without real blueprints):
```json
{
  "blueprint_id": "test_001",
  "walls": [
    {"type": "line", "start": [100, 100], "end": [500, 100], "is_load_bearing": false},
    {"type": "line", "start": [100, 100], "end": [100, 400], "is_load_bearing": false},
    {"type": "line", "start": [500, 100], "end": [500, 400], "is_load_bearing": false},
    {"type": "line", "start": [100, 400], "end": [500, 400], "is_load_bearing": false}
  ]
}
```

### Output: Detected Rooms

**Schema:**
```json
{
  "blueprint_id": "string",
  "processing_time_seconds": "number",
  "total_rooms_detected": "number",
  "rooms": [
    {
      "id": "string (unique identifier)",
      "bounding_box": [x_min, y_min, x_max, y_max],
      "confidence_score": "number (0-1, optional)",
      "type_hint": "string (optional: 'room', 'hallway', 'unknown')",
      "area_normalized": "number (optional)"
    }
  ]
}
```

**Example Output:**
```json
{
  "blueprint_id": "test_001",
  "processing_time_seconds": 12.4,
  "total_rooms_detected": 3,
  "rooms": [
    {
      "id": "room_001",
      "bounding_box": [50, 50, 300, 400],
      "confidence_score": 0.92,
      "type_hint": "room",
      "area_normalized": 62500
    },
    {
      "id": "room_002",
      "bounding_box": [350, 50, 700, 400],
      "confidence_score": 0.87,
      "type_hint": "room",
      "area_normalized": 122500
    },
    {
      "id": "hallway_001",
      "bounding_box": [300, 50, 350, 400],
      "confidence_score": 0.78,
      "type_hint": "hallway",
      "area_normalized": 17500
    }
  ]
}
```

---

## 10. Timeline & Milestones (Weekend Sprint)

### Day 1 (Saturday): Research & Foundation
**Target: 8 hours**

| Time | Milestone | Deliverables |
|------|-----------|--------------|
| 0-2h | Research & Tech Spike | AWS service evaluation, identify best detection approach |
| 2-4h | Mock Data Creation | 3-5 sample blueprints, expected output JSON |
| 4-6h | Backend Setup | AWS Lambda scaffolding, API Gateway config, basic "hello world" |
| 6-8h | Detection Logic v1 | Implement basic line/shape detection algorithm |

**Success Criteria:** Can process a simple blueprint and return SOMETHING (even if inaccurate)

---

### Day 2 (Sunday Morning): Core Development
**Target: 6 hours**

| Time | Milestone | Deliverables |
|------|-----------|--------------|
| 0-3h | Improve Detection Logic | Refine algorithm, handle edge cases, improve accuracy to 70%+ |
| 3-6h | Frontend Development | React upload component, blueprint display, overlay rendering |

**Success Criteria:** End-to-end flow works for at least one sample blueprint

---

### Day 2 (Sunday Afternoon): Polish & Demo Prep
**Target: 4 hours**

| Time | Milestone | Deliverables |
|------|-----------|--------------|
| 0-2h | Manual Correction UI | Add drag-to-resize, delete, and add room functionality |
| 2-3h | Testing & Bug Fixes | Test all sample blueprints, fix critical bugs |
| 3-4h | Demo Preparation | Polish UI, prepare talking points, record demo video |

**Success Criteria:** Demo-ready prototype that works reliably for 3+ blueprints

---

### Optional (Sunday Evening): Nice-to-Haves
**Target: 2 hours (if time permits)**
- Add confidence scores
- Improve UI styling
- Add room type hints
- Record polished demo video

---

## 11. Risks & Mitigation Strategies

### Technical Risks

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| **AWS AI services insufficient for detection** | MEDIUM | HIGH | Have fallback: Use OpenCV + Python for basic line detection |
| **Detection accuracy too low (< 70%)** | MEDIUM | HIGH | Focus on "good enough" demo, emphasize human-in-the-loop |
| **Processing time > 30 seconds** | LOW | MEDIUM | Optimize by reducing image resolution, simplify algorithm |
| **AWS free tier limits exceeded** | LOW | MEDIUM | Monitor usage closely, use mock data for testing |
| **Can't finish in weekend** | MEDIUM | HIGH | Ruthlessly cut scope - prioritize end-to-end flow over accuracy |

### Scope Risks

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| **Feature creep during development** | HIGH | MEDIUM | Stick to MVP list religiously, defer all "nice-to-haves" |
| **Over-engineering the solution** | MEDIUM | MEDIUM | Focus on demo quality, not production scalability |
| **Perfectionism blocking completion** | MEDIUM | HIGH | Set hard stop times, "good enough" > "perfect incomplete" |

### Demo Risks

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| **Demo blueprints don't work well** | MEDIUM | HIGH | Test multiple blueprints early, choose 3 that work best |
| **Live demo technical failure** | MEDIUM | HIGH | Record backup video demo, have screenshots ready |
| **Questions about production readiness** | HIGH | LOW | Acknowledge it's MVP, have clear "future enhancements" list |

---

## 12. Technical Approach Recommendations

### Recommended Detection Strategy (Weekend-Feasible)

**Option 1: AWS Textract + Custom Logic (Recommended)**
1. Use Amazon Textract to extract all lines/shapes from blueprint
2. Write custom algorithm to identify rectangular regions bounded by lines
3. Filter results to remove small spaces (closets) and merge hallways
4. Return bounding boxes for remaining regions

**Pros:** Leverages AWS, feasible in weekend, no ML training needed
**Cons:** May miss irregular rooms, requires custom logic

---

**Option 2: OpenCV + Python Lambda**
1. Use OpenCV's Hough Line Transform to detect wall lines
2. Use contour detection to identify closed regions
3. Filter by size and shape to identify rooms
4. Return bounding boxes

**Pros:** More control, well-documented approach, free
**Cons:** More code to write, may be slower

---

**Option 3: Pre-trained Object Detection (Stretch Goal)**
1. Use pre-trained YOLO or Mask R-CNN model fine-tuned on floor plans
2. Run inference via SageMaker endpoint
3. Return bounding boxes directly

**Pros:** Highest accuracy potential
**Cons:** Requires finding pre-trained model, may exceed weekend timeline

---

### Recommendation for Weekend MVP
**Start with Option 1 (Textract + Custom Logic), have Option 2 (OpenCV) as backup if Textract is insufficient.**

---

## 13. Open Questions

1. **What happens if user uploads a hand-drawn sketch?**
   → Out of scope for MVP - display clear error message

2. **Should the system auto-save corrections to a database?**
   → No database for MVP - just in-memory state and JSON export

3. **How do we handle multi-page PDFs (multi-floor buildings)?**
   → Out of scope - process first page only, or error message

4. **What if two rooms overlap (e.g., bathroom inside bedroom)?**
   → Accept both detections for MVP, let user delete false positives

5. **Should we integrate with existing Innergy room naming AI?**
   → No - keep as standalone demo, integration is future phase

---

## 14. Project Deliverables (Bootcamp Submission)

### Required Submissions

1. **GitHub Repository**
   - Clean, documented code
   - README with setup instructions
   - Sample blueprints included
   - Environment setup guide

2. **Working Demo**
   - Live deployed AWS service OR
   - Local demo with clear instructions
   - Video walkthrough (3-5 minutes)

3. **Technical Documentation (1-2 pages)**
   - Architecture diagram
   - AWS services used and configuration
   - Detection algorithm explanation
   - Known limitations and future improvements

4. **Demo Presentation**
   - Problem statement
   - Solution overview
   - Live demo with 3 sample blueprints
   - Accuracy metrics
   - Future roadmap

---

## 15. Appendix

### Sample Blueprints (Public Domain Sources)
- [Floor Plan Example 1](https://example.com/blueprint1.png) - Simple 3-room apartment
- [Floor Plan Example 2](https://example.com/blueprint2.png) - 5-room office layout
- [Floor Plan Example 3](https://example.com/blueprint3.png) - 10-room residential house

### References
- AWS Textract Documentation: https://docs.aws.amazon.com/textract/
- OpenCV Floor Plan Detection Tutorials: [Link]
- Computer Vision for Architecture: Research Papers

### Glossary
- **Bounding Box:** Smallest rectangle containing a detected room
- **False Positive:** System detects a "room" that isn't actually a room
- **False Negative:** System misses an actual room
- **Human-in-the-Loop:** User can manually correct AI errors
- **Normalized Coordinates:** Coordinates scaled to 0-1000 range regardless of image size

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| v0.1 | Nov 2025 | Original | Initial draft from bootcamp description |
| v1.0 | Nov 2025 | John (PM Agent) | Comprehensive refinement with clear definitions, metrics, scope, risks, and weekend timeline |

---

**Status:** Ready for Development ✅
**Next Steps:**
1. Review and approve PRD
2. Set up development environment
3. Begin Day 1 research and mock data creation
4. Execute weekend sprint plan
