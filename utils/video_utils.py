import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import os
from concurrent.futures import ThreadPoolExecutor
from skimage.transform import resize

def fast_ssim(frame1, frame2):
    """Compute SSIM on downscaled frames for performance improvement."""
    small_frame1 = resize(frame1, (frame1.shape[0] // 2, frame1.shape[1] // 2), anti_aliasing=True)
    small_frame2 = resize(frame2, (frame2.shape[0] // 2, frame2.shape[1] // 2), anti_aliasing=True)
    
    return ssim(small_frame1, small_frame2, data_range=1.0, full=False)

def fast_pixel_difference(prev_frame, current_frame):
    """Compute pixel difference efficiently using numpy."""
    diff = np.abs(prev_frame.astype(np.int16) - current_frame.astype(np.int16))
    return np.mean(diff) / 255 * 100

def encode_frame_fast(frame):
    """Encode frame as JPEG instead of PNG to improve speed."""
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return buffer.tobytes()

def save_frame(frame, frame_name, frame_dir):
    """Save frame to disk under the specified directory."""
    os.makedirs(frame_dir, exist_ok=True)
    cv2.imwrite(os.path.join(frame_dir, frame_name), frame, [cv2.IMWRITE_JPEG_QUALITY, 80])

def extract_frames(video_path, method, threshold, frame_dir):
    """Extract frames from video with optimized speed."""
    cap = cv2.VideoCapture(video_path)
    frames = {}
    prev_frame = None
    frame_count = 0

    def process_frame(frame_count, frame):
        frame_name = f'frame_{frame_count}.jpg'
        save_frame(frame, frame_name, frame_dir)
        return frame_name, encode_frame_fast(frame)

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_frame = {}

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if prev_frame is not None:
                if method == 'ssim':
                    score = fast_ssim(prev_frame, gray_frame)
                    if score < threshold:
                        future_to_frame[executor.submit(process_frame, frame_count, frame)] = frame_count
                elif method == 'pixel':
                    diff_percent = fast_pixel_difference(prev_frame, gray_frame)
                    if diff_percent/100 > threshold:
                        future_to_frame[executor.submit(process_frame, frame_count, frame)] = frame_count

            prev_frame = gray_frame
            frame_count += 1

        for future in future_to_frame:
            frame_name, encoded_frame = future.result()
            frames[frame_name] = encoded_frame

    cap.release()
    return frames
