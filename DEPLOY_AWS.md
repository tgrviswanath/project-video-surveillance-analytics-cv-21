# AWS Deployment Guide — Project CV-21 Video Surveillance Analytics

---

## AWS Services for Video Surveillance Analytics

### 1. Ready-to-Use AI (No Model Needed)

| Service                    | What it does                                                                 | When to use                                        |
|----------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Amazon Rekognition Video** | Detect people, vehicles, and objects across video — replace YOLOv8          | Replace your YOLOv8 + OpenCV video pipeline        |
| **Amazon Kinesis Video**   | Ingest and process live surveillance streams in real time                    | When you need live stream surveillance             |
| **Amazon Bedrock**         | Claude Vision for anomaly detection and alert generation via prompt          | When you need AI-generated surveillance reports    |

> **Amazon Rekognition Video** is the direct replacement for your YOLOv8 + OpenCV pipeline. It detects people, vehicles, and anomalies across video frames — no model download needed.

### 2. Host Your Own Model (Keep Current Stack)

| Service                    | What it does                                                        | When to use                                           |
|----------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **AWS App Runner**         | Run backend container — simplest, no VPC or cluster needed          | Quickest path to production                           |
| **Amazon ECS Fargate**     | Run backend + cv-service containers in a private VPC                | Best match for your current microservice architecture |
| **Amazon ECR**             | Store your Docker images                                            | Used with App Runner, ECS, or EKS                     |

### 3. Supporting Services

| Service                  | Purpose                                                                   |
|--------------------------|---------------------------------------------------------------------------|
| **Amazon S3**            | Store uploaded video files and surveillance reports                       |
| **Amazon DynamoDB**      | Store detection logs, anomaly alerts, and surveillance history            |
| **Amazon SNS**           | Send real-time alerts when anomalies are detected                         |
| **AWS Secrets Manager**  | Store API keys and connection strings instead of .env files               |
| **Amazon CloudWatch**    | Track processing latency, people counts, anomaly rates                    |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  S3 + CloudFront — React Frontend                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  AWS App Runner / ECS Fargate — Backend (FastAPI :8000)     │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ ECS Fargate       │    │ Amazon Rekognition Video           │
│ CV Service :8001  │    │ + Kinesis Video Streams            │
│ YOLOv8+OpenCV     │    │ Managed surveillance analytics     │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
aws configure
AWS_REGION=eu-west-2
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
```

---

## Step 1 — Create ECR and Push Images

```bash
aws ecr create-repository --repository-name surveillance/cv-service --region $AWS_REGION
aws ecr create-repository --repository-name surveillance/backend --region $AWS_REGION
ECR=$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR
docker build -f docker/Dockerfile.cv-service -t $ECR/surveillance/cv-service:latest ./cv-service
docker push $ECR/surveillance/cv-service:latest
docker build -f docker/Dockerfile.backend -t $ECR/surveillance/backend:latest ./backend
docker push $ECR/surveillance/backend:latest
```

---

## Step 2 — Create S3 Bucket and SNS Topic for Alerts

```bash
aws s3 mb s3://surveillance-videos-$AWS_ACCOUNT --region $AWS_REGION
aws sns create-topic --name surveillance-alerts --region $AWS_REGION
```

---

## Step 3 — Deploy with App Runner

```bash
aws apprunner create-service \
  --service-name surveillance-backend \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "'$ECR'/surveillance/backend:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "CV_SERVICE_URL": "http://cv-service:8001"
        }
      }
    }
  }' \
  --instance-configuration '{"Cpu": "2 vCPU", "Memory": "4 GB"}' \
  --region $AWS_REGION
```

---

## Option B — Use Amazon Rekognition Video

```python
import boto3, time

rekognition = boto3.client("rekognition", region_name="eu-west-2")
sns = boto3.client("sns", region_name="eu-west-2")

CROWD_THRESHOLD = 10
ALERT_TOPIC_ARN = "arn:aws:sns:eu-west-2:<account>:surveillance-alerts"

def analyze_surveillance_video(s3_bucket: str, s3_key: str) -> dict:
    job_id = rekognition.start_label_detection(
        Video={"S3Object": {"Bucket": s3_bucket, "Name": s3_key}},
        MinConfidence=60
    )["JobId"]
    while True:
        response = rekognition.get_label_detection(JobId=job_id)
        if response["JobStatus"] in ["SUCCEEDED", "FAILED"]:
            break
        time.sleep(5)
    people_count, alerts = 0, []
    for label in response.get("Labels", []):
        if label["Label"]["Name"] == "Person":
            people_count += 1
    if people_count > CROWD_THRESHOLD:
        alerts.append(f"Crowd detected: {people_count} people")
        sns.publish(TopicArn=ALERT_TOPIC_ARN, Message=f"ALERT: {alerts[0]}", Subject="Surveillance Alert")
    return {"people_count": people_count, "alerts": alerts, "status": "alert" if alerts else "normal"}
```

---

## Estimated Monthly Cost

| Service                    | Tier              | Est. Cost          |
|----------------------------|-------------------|--------------------|
| App Runner (backend)       | 2 vCPU / 4 GB     | ~$30–40/month      |
| App Runner (cv-service)    | 2 vCPU / 4 GB     | ~$30–40/month      |
| ECR + S3 + CloudFront      | Standard          | ~$3–7/month        |
| Rekognition Video          | Pay per minute    | ~$0.10/min         |
| Amazon SNS                 | Pay per message   | ~$1/month          |
| **Total (Option A)**       |                   | **~$63–87/month**  |
| **Total (Option B)**       |                   | **~$34–48/month + video cost** |

For exact estimates → https://calculator.aws

---

## Teardown

```bash
aws ecr delete-repository --repository-name surveillance/backend --force
aws ecr delete-repository --repository-name surveillance/cv-service --force
aws s3 rm s3://surveillance-videos-$AWS_ACCOUNT --recursive
aws s3 rb s3://surveillance-videos-$AWS_ACCOUNT
```
