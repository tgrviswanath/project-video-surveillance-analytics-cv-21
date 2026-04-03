from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

client = TestClient(app)

MOCK_RESULT = {
    "total_frames": 300,
    "analyzed_frames": 10,
    "duration_sec": 10.0,
    "fps": 30.0,
    "max_people_in_frame": 5,
    "avg_people_per_frame": 2.3,
    "total_detections": {"person": 23, "car": 4},
    "alerts": [{"frame": 60, "time_sec": 2.0, "type": "crowd", "detail": "12 people detected"}],
    "alert_count": 1,
    "frame_stats": [],
    "thumbnail": "base64string",
}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200


@patch("app.core.service.analyze_video", new_callable=AsyncMock, return_value=MOCK_RESULT)
def test_analyze_endpoint(mock_analyze):
    r = client.post(
        "/api/v1/analyze",
        files={"file": ("test.mp4", b"fakevideo", "video/mp4")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["alert_count"] == 1
    assert data["max_people_in_frame"] == 5
