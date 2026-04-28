import os
from django.core.exceptions import ValidationError
from PIL import Image

ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
MAX_IMAGE_SIZE_MB = 5


def validate_image_file(file):
    ext = os.path.splitext(file.name)[1].lower()

    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError("Only jpg, jpeg, png, webp files are allowed.")

    if file.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"Rasm hajmi dan kichik bo'lishi kerak {MAX_IMAGE_SIZE_MB} MB.")

    try:
        img = Image.open(file)
        img.verify()
    except Exception:
        raise ValidationError("Rasm fayli yaroqsiz.")