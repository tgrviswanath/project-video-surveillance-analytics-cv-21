# Project CV-21 - Video Surveillance Analytics

Microservice CV system that analyzes uploaded video files for object detection, people counting, and anomaly alerts using YOLOv8. Returns per-frame stats, a summary report, and an annotated thumbnail.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND  (React - Port 3000)                              │
│  axios POST /api/v1/analyze                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP JSON
┌──────────────────────▼──────────────────────────────────────┐
│  BACKEND  (FastAPI - Port 8000)                             │
│  httpx POST /api/v1/cv/analyze  →  calls cv-service         │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP JSON
┌──────────────────────▼──────────────────────────────────────┐
│  CV SERVICE  (FastAPI - Port 8001)                          │
│  OpenCV VideoCapture → sample frames → YOLOv8 detect        │
│  Count people/vehicles → detect anomalies → generate report │
│  Returns { summary, frame_stats[], alerts[], thumbnail }    │
└─────────────────────────────────────────────────────────────┘
```

---

## How It Works

```
Video uploaded
    ↓
OpenCV VideoCapture — sample every N frames
    ↓
YOLOv8 detection on each sampled frame
    ↓
Count people, vehicles, objects per frame
    ↓
Detect anomalies (crowd threshold, unknown objects)
    ↓
Return: summary + per-frame stats + annotated thumbnail (base64)
```

---

## Anomaly Detection Rules

| Anomaly | Trigger |
|---------|---------|
| Crowd alert | People count > threshold (default: 10) |
| Loitering | Same person detected in 80%+ of frames |
| Restricted object | Weapon/dangerous object detected |

---

## What's Different from CV-13 (Vehicle Tracking)

| | CV-13 Vehicle Tracking | CV-21 Surveillance Analytics |
|---|---|---|
| Input | Video stream / file | Video file |
| Task | Count + track vehicles | Multi-class detection + anomaly alerts |
| Model | YOLOv8 + DeepSORT | YOLOv8 (all classes) |
| Output | Vehicle count + tracks | Summary report + alerts + thumbnail |

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Frontend | React, MUI, Recharts |
| Backend | FastAPI, httpx |
| CV | YOLOv8, OpenCV |
| Input | MP4, AVI, MOV video files |
| Deployment | Docker, docker-compose |

---

## Prerequisites

- Python 3.12+
- Node.js — run `nvs use 20.14.0` before starting the frontend

---

## Local Run

### Step 1 — Start CV Service (Terminal 1)

```bash
cd cv-service
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
# YOLOv8n weights auto-downloaded by ultralytics on first run
```

Verify: http://localhost:8001/health → `{"status":"ok"}`

### Step 2 — Start Backend (Terminal 2)

```bash
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Step 3 — Start Frontend (Terminal 3)

```bash
cd frontend
npm install && npm start
```

Opens at: http://localhost:3000

---

## Environment Files

### `backend/.env`

```
APP_NAME=Video Surveillance Analytics API
APP_VERSION=1.0.0
ALLOWED_ORIGINS=["http://localhost:3000"]
CV_SERVICE_URL=http://localhost:8001
```

### `cv-service/.env`

```
MODEL_NAME=yolov8n.pt
FRAME_SAMPLE_RATE=5
CROWD_THRESHOLD=10
```

### `frontend/.env`

```
REACT_APP_API_URL=http://localhost:8000
```

---

## Docker Run

```bash
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API docs | http://localhost:8000/docs |
| CV Service docs | http://localhost:8001/docs |

---

## Run Tests

```bash
cd cv-service && venv\Scripts\activate
pytest ../tests/cv-service/ -v

cd backend && venv\Scripts\activate
pytest ../tests/backend/ -v
```

---

## Project Structure

```
project-video-surveillance-analytics-cv-21/
├── frontend/                    ← React (Port 3000)
├── backend/                     ← FastAPI (Port 8000)
├── cv-service/                  ← FastAPI CV (Port 8001)
│   └── app/
│       ├── api/routes.py
│       ├── core/analyzer.py     ← frame sampling + YOLOv8
│       ├── core/anomaly.py      ← crowd + loitering detection
│       └── main.py
├── samples/
├── tests/
├── docker/
└── docker-compose.yml
```

---

## API Reference

```
POST /api/v1/analyze
Body:     multipart/form-data { file: video }
Response: {
  "summary": { "total_frames": 120, "people_count": 8, "vehicles": 3 },
  "frame_stats": [{ "frame": 5, "people": 3, "vehicles": 1 }],
  "alerts": [{ "type": "crowd", "message": "10+ people detected at frame 45" }],
  "thumbnail": "<base64>"
}
```

---

## Dataset

Any MP4/AVI surveillance video. Try VIRAT or UCF-Crime datasets from Kaggle.
YOLOv8n weights auto-downloaded by ultralytics on first run.
