"""
Library API Router

Endpoints for managing the audio laboratory library and benchmarking.
"""

import logging
import shutil
import io
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, File, UploadFile, Request, Depends, Query
from pydantic import BaseModel

from api.middleware import limiter, verify_api_key
from detection import get_pipeline, convert_numpy_types
from sensors.utils import load_and_preprocess_audio
from telephony.pipeline import TelephonyPipeline
import soundfile as sf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/library", tags=["library"])

# Constants
LIBRARY_DIR = Path("backend/data/library")
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Ensure library directories exist
(LIBRARY_DIR / "organic").mkdir(parents=True, exist_ok=True)
(LIBRARY_DIR / "synthetic").mkdir(parents=True, exist_ok=True)


class LibraryFile(BaseModel):
    """File in the library."""
    filename: str
    label: str  # "organic" or "synthetic"
    size_bytes: int
    created_at: str
    analyzed: bool
    detection_score: Optional[float] = None
    sensor_details: Optional[Dict[str, Any]] = None


@router.post(
    "/upload",
    summary="Upload Audio to Library",
    description="Upload an audio file to the laboratory library with a ground truth label",
)
@limiter.limit("50/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="Audio file"),
    label: str = Query(..., regex="^(organic|synthetic)$", description="Ground truth label"),
    api_key: Optional[str] = Depends(verify_api_key),
):
    """
    Upload an audio file to the library.
    
    The file will be stored in `backend/data/library/{label}/{filename}`.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename missing")
            
        file_path = LIBRARY_DIR / label / file.filename
        
        # Check overwrite
        if file_path.exists():
             raise HTTPException(status_code=409, detail=f"File {file.filename} already exists in {label} library")
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"Uploaded {file.filename} to {label} library")
        
        return {"status": "success", "filename": file.filename, "label": label, "path": str(file_path)}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/files",
    response_model=List[LibraryFile],
    summary="List Library Files",
    description="List all files in the library with their analysis status",
)
@limiter.limit("100/minute")
async def list_files(
    request: Request,
    api_key: Optional[str] = Depends(verify_api_key),
):
    """List all files in the library."""
    files = []
    
    for label in ["organic", "synthetic"]:
        label_dir = LIBRARY_DIR / label
        if not label_dir.exists():
            continue
            
        for path in label_dir.glob("*"):
            if not path.is_file() or path.suffix == ".json":
                continue
                
            # Check for analysis file
            analysis_path = path.with_suffix(".json")
            analysis_data = None
            if analysis_path.exists():
                try:
                    with open(analysis_path, "r") as f:
                        analysis_data = json.load(f)
                except Exception:
                    logger.warning(f"Failed to load analysis for {path.name}")
            
            # Extract basic score info if available
            score = None
            sensor_details = None
            if analysis_data:
                score = analysis_data.get("detection_score")
                # Extract physics sensor details if present
                if "stage_results" in analysis_data and "physics_analysis" in analysis_data["stage_results"]:
                     sensor_details = analysis_data["stage_results"]["physics_analysis"].get("sensor_results")
            
            files.append(LibraryFile(
                filename=path.name,
                label=label,
                size_bytes=path.stat().st_size,
                created_at=datetime.fromtimestamp(path.stat().st_ctime).isoformat(),
                analyzed=analysis_path.exists(),
                detection_score=score,
                sensor_details=sensor_details
            ))
            
    return files


@router.post(
    "/analyze/{label}/{filename}",
    summary="Analyze Library File",
    description="Run full detection pipeline on a library file",
)
@limiter.limit("20/minute")
async def analyze_file(
    request: Request,
    label: str,
    filename: str,
    api_key: Optional[str] = Depends(verify_api_key),
):
    """
    Run detection pipeline on a specific library file.
    
    Saves the result as a .json file next to the audio file.
    """
    try:
        file_path = LIBRARY_DIR / label / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
            
        # Load and preprocess
        with open(file_path, "rb") as f:
            audio_io = io.BytesIO(f.read())
            audio_array, sr = load_and_preprocess_audio(audio_io)
        
        # Run pipeline
        pipeline = get_pipeline()
        result = pipeline.detect(audio_array, quick_mode=False)
        
        # Save result
        result_path = file_path.with_suffix(".json")
        with open(result_path, "w") as f:
            json.dump(convert_numpy_types(result), f, indent=2)
            
        return convert_numpy_types(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed for {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.post(
    "/simulate/{label}/{filename}",
    summary="Simulate Network Conditions",
    description="Degrade audio to simulate landline, mobile, or VoIP network conditions",
)
@limiter.limit("50/minute")
async def simulate_network(
    request: Request,
    label: str,
    filename: str,
    codec: str = Query(..., regex="^(landline|mobile|voip)$", description="Target network condition"),
    api_key: Optional[str] = Depends(verify_api_key),
):
    """
    Apply telephony simulation to a library file.
    Creates a new file with the suffix _{codec} in the same directory.
    """
    try:
        file_path = LIBRARY_DIR / label / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
            
        # Load audio
        with open(file_path, "rb") as f:
            audio_io = io.BytesIO(f.read())
            audio_array, sr = load_and_preprocess_audio(audio_io)
            
        # Apply simulation
        processed_audio = TelephonyPipeline.apply_codec_by_name(audio_array, sr, codec)
        
        # Save new file
        new_filename = f"{file_path.stem}_{codec}.wav"
        new_path = LIBRARY_DIR / label / new_filename
        
        # Check overwrite
        if new_path.exists():
             logger.info(f"Overwriting existing simulation {new_filename}")
             
        sf.write(str(new_path), processed_audio, sr)
        
        return {
            "status": "success",
            "original": filename,
            "new_file": new_filename,
            "codec": codec,
            "path": str(new_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation failed for {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
