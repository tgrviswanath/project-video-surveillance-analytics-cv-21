from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

MOCK_RESULT = {
    "total_frames": 90,
    "analyzed_frames": 3,
    "duration_sec": 3.0,
    "fps": 30.0,
    "max_people_in_frame": 2,
    "avg_people_per_frame": 1.0,
    "total_detections": {"person": 3},
    "alerts": [],
    "alert_count": 0,
    "frame_stats": [],
    "thumbnail": "base64string",
}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@patch("app.core.analyzer.analyze", return_value=MOCK_RESULT)
def test_analyze_video(mock_analyze):
    r = client.post(
        "/api/v1/cv/analyze",
        files={"file": ("test.mp4", b"fakevideo", "video/mp4")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "total_frames" in data
    assert "alerts" in data
    assert "thumbnail" in data


def test_analyze_unsupported_format():
    r = client.post(
        "/api/v1/cv/analyze",
        files={"file": ("test.jpg", b"fakejpg", "image/jpeg")},
    )
    assert r.status_code == 400


def test_analyze_empty_file():
    r = client.post(
        "/api/v1/cv/analyze",
        files={"file": ("test.mp4", b"", "video/mp4")},
    )
    assert r.status_code == 400
