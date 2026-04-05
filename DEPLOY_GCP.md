# GCP Deployment Guide — Project CV-21 Video Surveillance Analytics

---

## GCP Services for Video Surveillance Analytics

### 1. Ready-to-Use AI (No Model Needed)

| Service                              | What it does                                                                 | When to use                                        |
|--------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Video Intelligence API**           | Detect people, vehicles, and objects across video with timestamps            | Replace your YOLOv8 + OpenCV video pipeline        |
| **Vertex AI Vision**                 | Real-time video analytics pipeline for surveillance scenarios                | When you need live stream surveillance             |
| **Vertex AI Gemini Vision**          | Gemini Pro Vision for anomaly detection and alert generation via prompt      | When you need AI-generated surveillance reports    |

> **Video Intelligence API** is the direct replacement for your YOLOv8 + OpenCV pipeline. It detects people, vehicles, and activities across video — no model download needed.

### 2. Host Your Own Model (Keep Current Stack)

| Service                    | What it does                                                        | When to use                                           |
|----------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Cloud Run**              | Run backend + cv-service containers — serverless, scales to zero    | Best match for your current microservice architecture |
| **Artifact Registry**      | Store your Docker images                                            | Used with Cloud Run or GKE                            |

### 3. Supporting Services

| Service                        | Purpose                                                                   |
|--------------------------------|---------------------------------------------------------------------------|
| **Cloud Storage**              | Store uploaded video files and surveillance reports                       |
| **Firestore**                  | Store detection logs, anomaly alerts, and surveillance history            |
| **Cloud Pub/Sub**              | Send real-time alerts when anomalies are detected                         |
| **Secret Manager**             | Store API keys and connection strings instead of .env files               |
| **Cloud Monitoring + Logging** | Track processing latency, people counts, anomaly rates                    |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Firebase Hosting — React Frontend                          │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  Cloud Run — Backend (FastAPI :8000)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal HTTPS
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ Cloud Run         │    │ Video Intelligence API             │
│ CV Service :8001  │    │ Managed surveillance analytics     │
│ YOLOv8+OpenCV     │    │ No model download needed           │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
gcloud auth login
gcloud projects create surveillance-cv-project --name="Video Surveillance Analytics"
gcloud config set project surveillance-cv-project
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com videointelligence.googleapis.com \
  pubsub.googleapis.com firestore.googleapis.com \
  storage.googleapis.com cloudbuild.googleapis.com
```

---

## Step 1 — Create Artifact Registry and Push Images

```bash
GCP_REGION=europe-west2
gcloud artifacts repositories create surveillance-repo \
  --repository-format=docker --location=$GCP_REGION
gcloud auth configure-docker $GCP_REGION-docker.pkg.dev
AR=$GCP_REGION-docker.pkg.dev/surveillance-cv-project/surveillance-repo
docker build -f docker/Dockerfile.cv-service -t $AR/cv-service:latest ./cv-service
docker push $AR/cv-service:latest
docker build -f docker/Dockerfile.backend -t $AR/backend:latest ./backend
docker push $AR/backend:latest
```

---

## Step 2 — Create Cloud Storage and Pub/Sub for Alerts

```bash
gsutil mb -l $GCP_REGION gs://surveillance-videos-surveillance-cv-project
gcloud pubsub topics create surveillance-alerts
gcloud pubsub subscriptions create surveillance-alerts-sub --topic=surveillance-alerts
```

---

## Step 3 — Deploy to Cloud Run

```bash
gcloud run deploy cv-service \
  --image $AR/cv-service:latest --region $GCP_REGION \
  --port 8001 --no-allow-unauthenticated \
  --min-instances 1 --max-instances 3 --memory 4Gi --cpu 2

CV_URL=$(gcloud run services describe cv-service --region $GCP_REGION --format "value(status.url)")

gcloud run deploy backend \
  --image $AR/backend:latest --region $GCP_REGION \
  --port 8000 --allow-unauthenticated \
  --min-instances 1 --max-instances 5 --memory 1Gi --cpu 1 \
  --set-env-vars CV_SERVICE_URL=$CV_URL
```

---

## Option B — Use Video Intelligence API

```python
from google.cloud import videointelligence_v1 as vi, pubsub_v1
import json

vi_client = vi.VideoIntelligenceServiceClient()
publisher = pubsub_v1.PublisherClient()
TOPIC_PATH = publisher.topic_path("surveillance-cv-project", "surveillance-alerts")
CROWD_THRESHOLD = 10

def analyze_surveillance_video(gcs_uri: str) -> dict:
    operation = vi_client.annotate_video(
        request={
            "input_uri": gcs_uri,
            "features": [vi.Feature.OBJECT_TRACKING, vi.Feature.LABEL_DETECTION]
        }
    )
    result = operation.result(timeout=300)
    people_count = sum(
        1 for ann in result.annotation_results[0].object_annotations
        if ann.entity.description.lower() == "person"
    )
    alerts = []
    if people_count > CROWD_THRESHOLD:
        alerts.append(f"Crowd detected: {people_count} people")
        publisher.publish(TOPIC_PATH, json.dumps({"alert": alerts[0]}).encode())
    return {"people_count": people_count, "alerts": alerts, "status": "alert" if alerts else "normal"}
```

Add to requirements.txt: `google-cloud-videointelligence>=2.13.0 google-cloud-pubsub>=2.18.0`

---

## Estimated Monthly Cost

| Service                    | Tier                  | Est. Cost          |
|----------------------------|-----------------------|--------------------|
| Cloud Run (backend)        | 1 vCPU / 1 GB         | ~$10–15/month      |
| Cloud Run (cv-service)     | 2 vCPU / 4 GB         | ~$20–30/month      |
| Artifact Registry          | Storage               | ~$1–2/month        |
| Firebase Hosting           | Free tier             | $0                 |
| Video Intelligence API     | Pay per minute        | ~$0.10/min         |
| Cloud Pub/Sub              | Pay per message       | ~$1/month          |
| **Total (Option A)**       |                       | **~$32–48/month**  |
| **Total (Option B)**       |                       | **~$12–18/month + video cost** |

For exact estimates → https://cloud.google.com/products/calculator

---

## Teardown

```bash
gcloud run services delete backend --region $GCP_REGION --quiet
gcloud run services delete cv-service --region $GCP_REGION --quiet
gcloud artifacts repositories delete surveillance-repo --location=$GCP_REGION --quiet
gsutil rm -r gs://surveillance-videos-surveillance-cv-project
gcloud pubsub topics delete surveillance-alerts
gcloud projects delete surveillance-cv-project
```
