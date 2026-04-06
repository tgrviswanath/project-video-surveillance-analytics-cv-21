"""
Video surveillance analytics using YOLOv8.
- Samples frames from uploaded video
- Detects objects (people, vehicles, etc.) per frame
- Generates crowd alerts when person count exceeds threshold
- Returns summary stats + annotated thumbnail
"""
import cv2
import numpy as np
import base64
import tempfile
import os
from collections import defaultdict
from ultralytics import YOLO
from app.core.config import settings

_model = None

VEHICLE_CLASSES = {"car", "truck", "bus", "motorcycle", "bicycle"}
PERSON_CLASS = "person"


def _get_model():
    global _model
    if _model is None:
        try:
            _model = YOLO(settings.YOLO_MODEL)
        except Exception as e:
            raise FileNotFoundError(f"Surveillance model unavailable: {e}")
    return _model


def _frame_to_base64(frame: np.ndarray) -> str:
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return base64.b64encode(buf).decode("utf-8")


def analyze(video_bytes: bytes) -> dict:
    model = _get_model()

    # Write video to temp file (OpenCV needs a file path)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        duration_sec = round(total_frames / fps, 1)

        frame_stats = []
        alerts = []
        thumbnail = None
        frame_idx = 0
        max_people = 0
        total_detections = defaultdict(int)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % settings.SAMPLE_EVERY_N_FRAMES == 0:
                results = model(frame, conf=settings.CONFIDENCE_THRESHOLD, verbose=False)[0]
                class_counts = defaultdict(int)

                for box in results.boxes:
                    cls_name = model.names[int(box.cls)]
                    class_counts[cls_name] += 1
                    total_detections[cls_name] += 1

                people = class_counts.get(PERSON_CLASS, 0)
                vehicles = sum(class_counts.get(c, 0) for c in VEHICLE_CLASSES)

                if people > max_people:
                    max_people = people
                    thumbnail = _frame_to_base64(results.plot())

                if people >= settings.CROWD_THRESHOLD:
                    alerts.append({
                        "frame": frame_idx,
                        "time_sec": round(frame_idx / fps, 1),
                        "type": "crowd",
                        "detail": f"{people} people detected (threshold: {settings.CROWD_THRESHOLD})",
                    })

                frame_stats.append({
                    "frame": frame_idx,
                    "time_sec": round(frame_idx / fps, 1),
                    "people": people,
                    "vehicles": vehicles,
                    "objects": dict(class_counts),
                })

            frame_idx += 1

        cap.release()

        # If no thumbnail yet (no people), use first annotated frame
        if thumbnail is None and frame_stats:
            cap2 = cv2.VideoCapture(tmp_path)
            ret, frame = cap2.read()
            cap2.release()
            if ret:
                results = model(frame, conf=settings.CONFIDENCE_THRESHOLD, verbose=False)[0]
                thumbnail = _frame_to_base64(results.plot())

        avg_people = round(sum(s["people"] for s in frame_stats) / len(frame_stats), 1) if frame_stats else 0

        return {
            "total_frames": total_frames,
            "analyzed_frames": len(frame_stats),
            "duration_sec": duration_sec,
            "fps": round(fps, 1),
            "max_people_in_frame": max_people,
            "avg_people_per_frame": avg_people,
            "total_detections": dict(total_detections),
            "alerts": alerts,
            "alert_count": len(alerts),
            "frame_stats": frame_stats,
            "thumbnail": thumbnail,
        }
    finally:
        os.unlink(tmp_path)
