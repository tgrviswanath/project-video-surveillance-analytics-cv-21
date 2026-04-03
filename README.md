# Project 21 - Video Surveillance Analytics (CV)

Analyzes uploaded video files for object detection, people counting, and anomaly alerts using YOLOv8. Returns per-frame stats and a summary report.

## Architecture

```
Frontend :3000  →  Backend :8000  →  CV Service :8001
  React/MUI        FastAPI/httpx      FastAPI/YOLOv8/OpenCV
```

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

## What's Different from Earlier Projects

| | Project 13 (Vehicle Tracking) | Project 21 (Surveillance Analytics) |
|---|---|---|
| Input | Video stream / file | Video file |
| Task | Count + track vehicles | Multi-class detection + anomaly alerts |
| Model | YOLOv8 + DeepSORT | YOLOv8 (all classes) |
| Output | Vehicle count + tracks | Summary report + alerts + thumbnail |

## Local Run

```bash
# Terminal 1 - CV Service
cd cv-service && python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Terminal 2 - Backend
cd backend && python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 3 - Frontend
cd frontend && npm install && npm start
```

- CV Service docs: http://localhost:8001/docs
- Backend docs:   http://localhost:8000/docs
- UI:             http://localhost:3000

## Docker

```bash
docker-compose up --build
```

## Dataset
Any MP4/AVI surveillance video. Try VIRAT or UCF-Crime datasets from Kaggle.
YOLOv8n weights auto-downloaded by ultralytics on first run.
