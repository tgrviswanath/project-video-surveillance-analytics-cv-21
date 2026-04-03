from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "Video Surveillance Analytics CV Service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8001
    YOLO_MODEL: str = "yolov8n.pt"
    SAMPLE_EVERY_N_FRAMES: int = 30   # analyze 1 frame per second at 30fps
    CONFIDENCE_THRESHOLD: float = 0.4
    CROWD_THRESHOLD: int = 10         # alert if people count exceeds this

    class Config:
        env_file = ".env"


settings = Settings()
