from fastapi import APIRouter, HTTPException, UploadFile, File
from app.core.analyzer import analyze

router = APIRouter(prefix="/api/v1/cv", tags=["surveillance"])

ALLOWED = {"mp4", "avi", "mov", "mkv", "webm"}


def _validate(filename: str):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED:
        raise HTTPException(status_code=400, detail=f"Unsupported format: .{ext}")


@router.post("/analyze")
async def analyze_video(file: UploadFile = File(...)):
    _validate(file.filename)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    return analyze(content)
