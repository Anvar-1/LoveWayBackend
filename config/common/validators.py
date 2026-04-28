import os
import re
from django.core.exceptions import ValidationError
from rest_framework import serializers
from PIL import Image

ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
MAX_IMAGE_SIZE_MB = 5


def validate_strong_password(password: str):
    if len(password) < 8:
        raise serializers.ValidationError("Password must be at least 8 characters long.")

    if password.isdigit():
        raise serializers.ValidationError("Password cannot contain only numbers.")

    if not re.search(r"[A-Z]", password):
        raise serializers.ValidationError("Password must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        raise serializers.ValidationError("Password must contain at least one lowercase letter.")

    if not re.search(r"\d", password):
        raise serializers.ValidationError("Password must contain at least one number.")

    if not re.search(r"[^\w\s]", password):
        raise serializers.ValidationError("Password must contain at least one special character.")

    common_weak_passwords = {
        "12345678", "password", "password123", "qwerty123",
        "admin123", "11111111", "00000000"
    }

    if password.lower() in common_weak_passwords:
        raise serializers.ValidationError("This password is too common. Choose a stronger password.")

    return password


def validate_image_file(file):
    ext = os.path.splitext(file.name)[1].lower()

    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError("Only jpg, jpeg, png, webp files are allowed.")

    if file.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"Image size must be less than {MAX_IMAGE_SIZE_MB} MB.")

    try:
        img = Image.open(file)
        img.verify()
    except Exception:
        raise ValidationError("Invalid image file.")