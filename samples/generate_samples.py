"""
Generate sample videos for cv-21 Video Surveillance Analytics.
Run: pip install opencv-python-headless numpy && python generate_samples.py
Output: 3 MP4 videos — normal crowd, crowd alert (>10 people), empty scene.
"""
import cv2
import numpy as np
import os, math

OUT = os.path.dirname(__file__)
W, H, FPS, FRAMES = 640, 480, 25, 150


def save_video(frames, name):
    path = os.path.join(OUT, name)
    out = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    for f in frames:
        out.write(f)
    out.release()
    print(f"  created: {name}  ({len(frames)} frames)")


def draw_person(img, x, y, h=60, color=(60, 120, 200)):
    head_r = h // 6
    cv2.circle(img, (x, y), head_r, (220, 180, 140), -1)
    cv2.rectangle(img, (x - head_r, y + head_r), (x + head_r, y + h // 2), color, -1)
    cv2.line(img, (x, y + h // 2), (x - head_r, y + h), (80, 60, 40), 2)
    cv2.line(img, (x, y + h // 2), (x + head_r, y + h), (80, 60, 40), 2)


def draw_car(img, x, y, color=(50, 50, 200)):
    cv2.rectangle(img, (x, y + 15), (x + 100, y + 45), color, -1)
    pts = np.array([[x + 15, y + 15], [x + 25, y], [x + 75, y], [x + 85, y + 15]], np.int32)
    cv2.fillPoly(img, [pts], color)
    cv2.circle(img, (x + 20, y + 48), 10, (30, 30, 30), -1)
    cv2.circle(img, (x + 80, y + 48), 10, (30, 30, 30), -1)


def scene_background():
    img = np.full((H, W, 3), (80, 80, 80), dtype=np.uint8)
    # pavement
    cv2.rectangle(img, (0, 300), (W, H), (100, 100, 100), -1)
    # building
    cv2.rectangle(img, (0, 0), (200, 300), (160, 150, 140), -1)
    cv2.rectangle(img, (440, 0), (W, 300), (150, 140, 130), -1)
    # windows
    for bx, bw in [(0, 200), (440, 200)]:
        for wy in range(20, 280, 50):
            for wx in range(bx + 15, bx + bw - 15, 40):
                cv2.rectangle(img, (wx, wy), (wx + 25, wy + 30), (180, 220, 255), -1)
    return img


def normal_crowd_video():
    """5 people walking — below crowd threshold."""
    people = [{"x": i * 100 + 50, "speed": 2 + i * 0.5, "color": (60 + i * 30, 100, 180)} for i in range(5)]
    frames = []
    for f in range(FRAMES):
        img = scene_background()
        for p in people:
            p["x"] = int((p["x"] + p["speed"])) % W
            draw_person(img, p["x"], 310, color=p["color"])
        cv2.putText(img, f"People: {len(people)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        frames.append(img)
    return frames


def crowd_alert_video():
    """12 people — triggers crowd alert (threshold=10)."""
    people = [{"x": i * 50 + 20, "speed": 1.5 + (i % 3) * 0.5,
               "color": (50 + (i * 20) % 180, 80 + (i * 15) % 120, 150)} for i in range(12)]
    frames = []
    for f in range(FRAMES):
        img = scene_background()
        for p in people:
            p["x"] = int((p["x"] + p["speed"])) % W
            draw_person(img, p["x"], 310, color=p["color"])
        cv2.putText(img, f"People: {len(people)} - CROWD ALERT", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        # red border alert
        cv2.rectangle(img, (0, 0), (W - 1, H - 1), (0, 0, 255), 4)
        frames.append(img)
    return frames


def empty_scene_video():
    """Empty scene with a car passing — no people."""
    car = {"x": -110, "speed": 5}
    frames = []
    for f in range(FRAMES):
        img = scene_background()
        car["x"] = (car["x"] + car["speed"]) % (W + 110) - 110
        draw_car(img, car["x"], 310, color=(50, 100, 200))
        cv2.putText(img, "People: 0", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        frames.append(img)
    return frames


if __name__ == "__main__":
    print("Generating cv-21 samples...")
    save_video(normal_crowd_video(), "sample_normal_crowd.mp4")
    save_video(crowd_alert_video(), "sample_crowd_alert.mp4")
    save_video(empty_scene_video(), "sample_empty_scene.mp4")
    print("Done — 3 videos in samples/")
    print("Tip: sample_crowd_alert.mp4 should trigger crowd alerts in the system.")
