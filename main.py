from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from utils.video_utils import extract_frames
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow requests from React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/extract-frames")
async def extract_frames_api(video_file: UploadFile = File(...), method: str = 'ssim', threshold: float = 0.8):
    # Validate method
    if method not in ['ssim', 'pixel']:
        raise HTTPException(status_code=400, detail="Invalid method. Use 'ssim' or 'pixel'.")

    # Validate threshold
    if not (0 <= threshold <= 1):
        raise HTTPException(status_code=400, detail="Threshold must be between 0 and 1.")

    try:
        # Save uploaded video temporarily
        video_path = f"temp_{video_file.filename}"
        with open(video_path, "wb") as buffer:
            buffer.write(video_file.file.read())

        # Extract frames
        frames = extract_frames(video_path, method, threshold)

        # Clean up temporary video file
        os.remove(video_path)

        # Return frame names and URLs
        frame_urls = {name: f"/get-frame/{name}" for name in frames.keys()}
        return JSONResponse(content={"frames": frame_urls})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-frame/{frame_name}")
async def get_frame(frame_name: str):
    """Serve a specific frame as an image."""
    frame_path = f"storage/{frame_name}"
    if not os.path.exists(frame_path):
        raise HTTPException(status_code=404, detail="Frame not found.")
    return StreamingResponse(open(frame_path, "rb"), media_type="image/png")