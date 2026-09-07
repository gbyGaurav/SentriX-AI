"""Video processing module using OpenCV.
Samples frames efficiently (e.g. 1 frame every N seconds) and extracts video metadata.
Never loads the whole video into memory.
"""

import os
import tempfile
import logging
from typing import Dict, List, Any, Tuple
import cv2

logger = logging.getLogger(__name__)


def sample_video_frames(
    video_bytes: bytes,
    max_frames: int = 4,
    sample_rate_sec: float = 3.0
) -> Dict[str, Any]:
    """Saves video temporarily, extracts metadata and samples representative frames.
    Downsamples frames to max 720p to preserve memory on 512MB RAM environments.
    Returns:
        {
            "metadata": {...},
            "frames": [(timestamp_sec, frame_jpeg_bytes), ...],
            "frame_count": int,
            "duration_sec": float,
            "error": str | None
        }
    """
    import gc
    result = {
        "metadata": {},
        "frames": [],
        "frame_count": 0,
        "duration_sec": 0.0,
        "error": None,
    }

    # Write to a temporary file safely
    temp_video_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_file.write(video_bytes)
            temp_video_path = temp_file.name

        cap = cv2.VideoCapture(temp_video_path)
        if not cap.isOpened():
            result["error"] = "Could not open video file."
            return result

        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        duration_sec = total_frames / fps if fps > 0 else 0.0

        result["metadata"] = {
            "fps": round(fps, 2),
            "total_frames": total_frames,
            "width": width,
            "height": height,
            "duration_sec": round(duration_sec, 2),
        }
        result["duration_sec"] = round(duration_sec, 2)

        # Frame step
        step_frames = max(1, int(fps * sample_rate_sec))
        sampled_frames = []

        current_frame = 0
        while cap.isOpened() and len(sampled_frames) < max_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            timestamp = round(current_frame / fps, 2)

            # Resize frame to max 720p for memory preservation
            if max(frame.shape[0], frame.shape[1]) > 720:
                scale = 720.0 / max(frame.shape[0], frame.shape[1])
                frame = cv2.resize(frame, (int(frame.shape[1] * scale), int(frame.shape[0] * scale)), interpolation=cv2.INTER_AREA)

            # Encode frame to compact JPEG
            success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if success:
                sampled_frames.append((timestamp, buffer.tobytes()))

            del frame
            current_frame += step_frames
            if current_frame >= total_frames:
                break

        cap.release()
        gc.collect()
        result["frames"] = sampled_frames
        result["frame_count"] = len(sampled_frames)

    except Exception as e:
        logger.error(f"Error processing video: {e}", exc_info=True)
        result["error"] = str(e)
    finally:
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
            except Exception:
                pass

    return result
