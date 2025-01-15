import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import os

def encode_frame(frame):
    """Encode frame as PNG."""
    _, buffer = cv2.imencode('.png', frame)
    return buffer.tobytes()

def extract_frames(video_path, method, threshold, frame_dir):
    """Extract frames from video based on similarity threshold."""
    cap = cv2.VideoCapture(video_path)
    frames = {}
    prev_frame = None
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_frame is not None:
            if method == 'ssim':
                score, _ = ssim(prev_frame, gray_frame, full=True)
                if score < threshold:
                    frame_name = f'frame_{frame_count}.png'
                    frames[frame_name] = encode_frame(frame)
                    save_frame(frame, frame_name, frame_dir)
            elif method == 'pixel':
                diff = cv2.absdiff(prev_frame, gray_frame)
                diff_percent = (np.count_nonzero(diff) / diff.size) * 100
                if diff_percent > threshold:
                    frame_name = f'frame_{frame_count}.png'
                    frames[frame_name] = encode_frame(frame)
                    save_frame(frame, frame_name, frame_dir)

        prev_frame = gray_frame
        frame_count += 1

    cap.release()
    return frames

def save_frame(frame, frame_name, frame_dir):
    """Save frame to disk under the specified directory."""
    if not os.path.exists(frame_dir):
        os.makedirs(frame_dir)
    cv2.imwrite(os.path.join(frame_dir, frame_name), frame)