from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel
import subprocess
import logging
from pathlib import Path
from typing import Optional, List

router = APIRouter(prefix="/api/factory", tags=["factory"])

logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_FILE = PROJECT_ROOT / "logs" / "factory_latest.log"
DATA_FACTORY_SCRIPT = PROJECT_ROOT / "data_factory.py"

# Ensure log dir exists
LOG_FILE.parent.mkdir(exist_ok=True)

class GenerateRequest(BaseModel):
    count: int = 5
    service: str = "openai"  # openai, elevenlabs, all
    augment: bool = True
    dry_run: bool = False

class AugmentRequest(BaseModel):
    count: int = 10
    all_files: bool = False

class TestRequest(BaseModel):
    count: int = 50

def run_command_in_background(command: List[str]):
    """Run a command and redirect output to the log file."""
    try:
        # Clear log file
        with open(LOG_FILE, "w") as f:
            f.write(f"--- Starting Command: {' '.join(command)} ---\n")
        
        # Open file for appending output
        with open(LOG_FILE, "a") as f:
            # We use a shell wrapper to ensure env vars are loaded if needed, 
            # but direct execution is safer. Using subprocess.run for simplicity 
            # if we wanted blocking, but for background we use Popen.
            process = subprocess.Popen(
                command,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=PROJECT_ROOT
            )
            process.wait()
            f.write("\n--- Job Completed ---\n")
            
    except Exception as e:
        logger.error(f"Background task failed: {e}")
        with open(LOG_FILE, "a") as f:
            f.write(f"\n[ERROR] Task failed: {e}\n")

@router.post("/generate")
async def generate_data(req: GenerateRequest, background_tasks: BackgroundTasks):
    cmd = [
        str(DATA_FACTORY_SCRIPT),
        "generate",
        "--count", str(req.count),
        "--service", req.service
    ]
    if req.augment:
        cmd.append("--augment")
    if req.dry_run:
        cmd.append("--dry-run")
        
    background_tasks.add_task(run_command_in_background, cmd)
    return {"status": "started", "job": "generation", "details": f"Generating {req.count} samples"}

@router.post("/augment")
async def augment_data(req: AugmentRequest, background_tasks: BackgroundTasks):
    cmd = [
        str(DATA_FACTORY_SCRIPT),
        "augment",
        "--count", str(req.count)
    ]
    if req.all_files:
        cmd.append("--all")
        
    background_tasks.add_task(run_command_in_background, cmd)
    return {"status": "started", "job": "augmentation", "details": f"Augmenting {req.count if not req.all_files else 'ALL'} files"}

@router.post("/test")
async def run_test(req: TestRequest, background_tasks: BackgroundTasks):
    cmd = [
        str(DATA_FACTORY_SCRIPT),
        "test",
        "--count", str(req.count)
    ]
    background_tasks.add_task(run_command_in_background, cmd)
    return {"status": "started", "job": "testing", "details": f"Running micro-test on {req.count} samples"}

@router.get("/logs")
async def get_logs():
    """Return the content of the factory log file."""
    if not LOG_FILE.exists():
        return {"logs": "No active job logs."}
    
    try:
        with open(LOG_FILE, "r") as f:
            content = f.read()
        return {"logs": content}
    except Exception as e:
        return {"logs": f"Error reading logs: {e}"}
