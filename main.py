from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from utils.video_utils import extract_frames
import os
import uuid
import shutil
import time
from datetime import datetime, timedelta
from typing import Dict, List

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow requests from React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary storage directory
TEMP_STORAGE = "storage"
os.makedirs(TEMP_STORAGE, exist_ok=True)

# In-memory background task storage
background_tasks_storage: Dict[str, Dict] = {}

def delete_frames_after_delay(unique_id: str, delay_minutes: int = 10):
    """Delete frames after a specified delay."""
    time.sleep(delay_minutes * 60)  # Convert minutes to seconds
    frame_dir = os.path.join(TEMP_STORAGE, unique_id)
    if os.path.exists(frame_dir):
        shutil.rmtree(frame_dir)
    # Update background task status to "completed"
    background_tasks_storage[unique_id]["status"] = "completed"
    background_tasks_storage[unique_id]["end_time"] = datetime.now().isoformat()

@app.post("/extract-frames")
async def extract_frames_api(
    video_file: UploadFile = File(...),
    method: str = 'ssim',
    threshold: float = 0.8,
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    # Validate method
    if method not in ['ssim', 'pixel']:
        raise HTTPException(
            status_code=400,
            detail="Invalid method. Use 'ssim' or 'pixel'."
        )

    # Validate threshold
    if not (0 <= threshold <= 1):
        raise HTTPException(
            status_code=400,
            detail="Threshold must be between 0 and 1."
        )

    try:
        # Generate a unique ID for this video
        unique_id = str(uuid.uuid4())

        # Save uploaded video temporarily
        video_path = f"temp_{video_file.filename}"
        with open(video_path, "wb") as buffer:
            buffer.write(video_file.file.read())

        # Extract frames and save them under the unique ID directory
        frame_dir = os.path.join(TEMP_STORAGE, unique_id)
        os.makedirs(frame_dir, exist_ok=True)
        frames = extract_frames(video_path, method, threshold, frame_dir)

        # Clean up temporary video file
        os.remove(video_path)

        # Schedule deletion of frames after 30 minutes
        background_tasks.add_task(delete_frames_after_delay, unique_id)

        # Store background task information
        background_tasks_storage[unique_id] = {
            "status": "pending",
            "start_time": datetime.now().isoformat(),  # Serialize datetime to string
            "end_time": None,
            "frames": list(frames.keys()),
        }

        # Return unique ID and frame URLs
        frame_urls = {name: f"/get-frame/{unique_id}/{name}" for name in frames.keys()}
        return JSONResponse(content={"unique_id": unique_id, "frames": frame_urls})

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the video: {str(e)}"
        )

@app.get("/get-frame/{unique_id}/{frame_name}")
async def get_frame(unique_id: str, frame_name: str):
    """Serve a specific frame as an image."""
    frame_path = os.path.join(TEMP_STORAGE, unique_id, frame_name)
    if not os.path.exists(frame_path):
        raise HTTPException(
            status_code=404,
            detail="Frame not found. It may have been deleted or never existed."
        )
    return StreamingResponse(open(frame_path, "rb"), media_type="image/png")

@app.get("/background-tasks")
async def list_background_tasks():
    """List all background tasks."""
    # Convert datetime objects to strings for JSON serialization
    serialized_tasks = {
        task_id: {
            **task,
            "start_time": task["start_time"],  # Already serialized
            "end_time": task["end_time"],      # Already serialized or None
        }
        for task_id, task in background_tasks_storage.items()
    }
    return JSONResponse(content=serialized_tasks)

@app.get("/background-tasks/{unique_id}")
async def get_background_task_status(unique_id: str):
    """Get the status of a specific background task."""
    if unique_id not in background_tasks_storage:
        raise HTTPException(
            status_code=404,
            detail="Background task not found."
        )
    # Convert datetime objects to strings for JSON serialization
    task = background_tasks_storage[unique_id]
    serialized_task = {
        **task,
        "start_time": task["start_time"],  # Already serialized
        "end_time": task["end_time"],      # Already serialized or None
    }
    return JSONResponse(content=serialized_task)

# Custom exception handler for 404 errors
@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found."}
    )

# Custom exception handler for 500 errors
@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."}
    )