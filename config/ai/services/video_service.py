import os
import subprocess
import tempfile
from django.core.files.uploadedfile import UploadedFile
from django.core.files import File

from .moderation_service import moderate_image


def save_temp_video(uploaded_file: UploadedFile) -> str:
    suffix = os.path.splitext(uploaded_file.name)[-1] or ".mp4"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    for chunk in uploaded_file.chunks():
        tmp.write(chunk)
    tmp.flush()
    tmp.close()
    return tmp.name


def extract_frames(video_path: str, output_dir: str, fps: int = 1) -> list[str]:
    output_pattern = os.path.join(output_dir, "frame_%03d.jpg")
    subprocess.run(
        [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"fps={fps}",
            output_pattern,
            "-y",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    files = sorted(
        os.path.join(output_dir, f)
        for f in os.listdir(output_dir)
        if f.endswith(".jpg")
    )
    return files


def moderate_video(uploaded_file: UploadedFile) -> dict:
    video_path = save_temp_video(uploaded_file)

    try:
        with tempfile.TemporaryDirectory() as frames_dir:
            frame_paths = extract_frames(video_path, frames_dir, fps=1)

            for frame_path in frame_paths[:20]:
                with open(frame_path, "rb") as f:
                    django_file = File(f, name=os.path.basename(frame_path))
                    django_file.content_type = "image/jpeg"
                    result = moderate_image(django_file)

                    if result["sexual"] or result["sexual_minors"]:
                        return {
                            "status": "rejected",
                            "reason": "adult_content"
                        }

        return {"status": "approved"}

    finally:
        if os.path.exists(video_path):
            os.remove(video_path)