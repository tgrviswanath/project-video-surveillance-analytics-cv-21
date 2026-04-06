import asyncio
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.core.analyzer import analyze
from app.core.validate import validate_video

router = APIRouter(prefix="/api/v1/cv", tags=["surveillance"])


@router.post("/analyze")
async def analyze_video(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    validate_video(file, content)
    try:
        return await asyncio.get_running_loop().run_in_executor(None, analyze, content)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {e}")
