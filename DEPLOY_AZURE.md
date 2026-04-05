# Azure Deployment Guide — Project CV-21 Video Surveillance Analytics

---

## Azure Services for Video Surveillance Analytics

### 1. Ready-to-Use AI (No Model Needed)

| Service                              | What it does                                                                 | When to use                                        |
|--------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Azure AI Video Indexer**           | Detect people, vehicles, and objects across video with timestamps            | Replace your YOLOv8 + OpenCV video pipeline        |
| **Azure Video Analyzer**             | Real-time video analytics pipeline for surveillance scenarios                | When you need live stream surveillance             |
| **Azure OpenAI Vision**              | GPT-4V for anomaly detection and alert generation via prompt                 | When you need AI-generated surveillance reports    |

> **Azure AI Video Indexer** is the direct replacement for your YOLOv8 + OpenCV pipeline. It detects people, vehicles, and activities across video — no model download needed.

### 2. Host Your Own Model (Keep Current Stack)

| Service                        | What it does                                                        | When to use                                           |
|--------------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Azure Container Apps**       | Run your 3 Docker containers (frontend, backend, cv-service)        | Best match for your current microservice architecture |
| **Azure Container Registry**   | Store your Docker images                                            | Used with Container Apps or AKS                       |

### 3. Supporting Services

| Service                       | Purpose                                                                  |
|-------------------------------|--------------------------------------------------------------------------|
| **Azure Blob Storage**        | Store uploaded video files and surveillance reports                      |
| **Azure Cosmos DB**           | Store detection logs, anomaly alerts, and surveillance history           |
| **Azure Event Grid**          | Send real-time alerts when anomalies are detected                        |
| **Azure Key Vault**           | Store API keys and connection strings instead of .env files              |
| **Azure Monitor + App Insights** | Track processing latency, people counts, anomaly rates               |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Azure Static Web Apps — React Frontend                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  Azure Container Apps — Backend (FastAPI :8000)             │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ Container Apps    │    │ Azure AI Video Indexer             │
│ CV Service :8001  │    │ Managed surveillance analytics     │
│ YOLOv8+OpenCV     │    │ No model download needed           │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
az login
az group create --name rg-video-surveillance --location uksouth
az extension add --name containerapp --upgrade
```

---

## Step 1 — Create Container Registry and Push Images

```bash
az acr create --resource-group rg-video-surveillance --name surveillanceacr --sku Basic --admin-enabled true
az acr login --name surveillanceacr
ACR=surveillanceacr.azurecr.io
docker build -f docker/Dockerfile.cv-service -t $ACR/cv-service:latest ./cv-service
docker push $ACR/cv-service:latest
docker build -f docker/Dockerfile.backend -t $ACR/backend:latest ./backend
docker push $ACR/backend:latest
```

---

## Step 2 — Create Blob Storage for Videos

```bash
az storage account create --name surveillancevideos --resource-group rg-video-surveillance --sku Standard_LRS
az storage container create --name videos --account-name surveillancevideos
az storage container create --name reports --account-name surveillancevideos
```

---

## Step 3 — Deploy Container Apps

```bash
az containerapp env create --name surveillance-env --resource-group rg-video-surveillance --location uksouth

az containerapp create \
  --name cv-service --resource-group rg-video-surveillance \
  --environment surveillance-env --image $ACR/cv-service:latest \
  --registry-server $ACR --target-port 8001 --ingress internal \
  --min-replicas 1 --max-replicas 3 --cpu 2 --memory 4.0Gi

az containerapp create \
  --name backend --resource-group rg-video-surveillance \
  --environment surveillance-env --image $ACR/backend:latest \
  --registry-server $ACR --target-port 8000 --ingress external \
  --min-replicas 1 --max-replicas 5 --cpu 0.5 --memory 1.0Gi \
  --env-vars CV_SERVICE_URL=http://cv-service:8001
```

---

## Option B — Use Azure AI Video Indexer

```python
import requests, time

VI_ACCOUNT_ID = os.getenv("VIDEO_INDEXER_ACCOUNT_ID")
VI_LOCATION = "trial"
VI_API_KEY = os.getenv("VIDEO_INDEXER_API_KEY")
CROWD_THRESHOLD = 10

def analyze_surveillance_video(video_url: str, video_name: str) -> dict:
    token_url = f"https://api.videoindexer.ai/auth/{VI_LOCATION}/Accounts/{VI_ACCOUNT_ID}/AccessToken?allowEdit=true"
    token = requests.get(token_url, headers={"Ocp-Apim-Subscription-Key": VI_API_KEY}).json()
    upload_url = f"https://api.videoindexer.ai/{VI_LOCATION}/Accounts/{VI_ACCOUNT_ID}/Videos?name={video_name}&videoUrl={video_url}&accessToken={token}"
    video_id = requests.post(upload_url).json()["id"]
    # Poll for completion
    while True:
        token = requests.get(token_url, headers={"Ocp-Apim-Subscription-Key": VI_API_KEY}).json()
        index_url = f"https://api.videoindexer.ai/{VI_LOCATION}/Accounts/{VI_ACCOUNT_ID}/Videos/{video_id}/Index?accessToken={token}"
        index = requests.get(index_url).json()
        if index.get("state") == "Processed":
            break
        time.sleep(10)
    insights = index.get("videos", [{}])[0].get("insights", {})
    labels = insights.get("labels", [])
    people_count = sum(len(l.get("instances", [])) for l in labels if l["name"].lower() == "person")
    alerts = []
    if people_count > CROWD_THRESHOLD:
        alerts.append(f"Crowd detected: {people_count} people")
    return {"people_count": people_count, "alerts": alerts, "status": "alert" if alerts else "normal", "video_id": video_id}
```

---

## Estimated Monthly Cost

| Service                  | Tier      | Est. Cost          |
|--------------------------|-----------|--------------------|
| Container Apps (backend) | 0.5 vCPU  | ~$10–15/month      |
| Container Apps (cv-svc)  | 2 vCPU    | ~$25–35/month      |
| Container Registry       | Basic     | ~$5/month          |
| Static Web Apps          | Free      | $0                 |
| Azure Video Indexer      | Pay per minute | ~$0.15/min    |
| **Total (Option A)**     |           | **~$40–55/month**  |
| **Total (Option B)**     |           | **~$15–25/month + video cost** |

For exact estimates → https://calculator.azure.com

---

## Teardown

```bash
az group delete --name rg-video-surveillance --yes --no-wait
```
