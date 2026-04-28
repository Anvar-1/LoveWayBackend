from django.conf import settings
from django.db import models
from django.utils import timezone
from .validators import validate_image_file


class Profile(models.Model):
    GENDER_CHOICES = (
        ("male", "Male"),
        ("female", "Female"),
    )

    MARITAL_STATUS_CHOICES = (
        ("single", "Single"),
        ("divorced", "Divorced"),
        ("widowed", "Widowed"),
        ("married", "Married"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    full_name = models.CharField(max_length=255, blank=True)
    username = models.CharField(max_length=50, unique=True, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)

    bio = models.TextField(blank=True)

    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, null=True)

    marital_status = models.CharField(
        max_length=20,
        choices=MARITAL_STATUS_CHOICES,
        blank=True
    )

    has_children = models.BooleanField(default=False)
    children_count = models.PositiveIntegerField(default=0)

    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    avatar = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        validators=[validate_image_file]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_age(self):
        if not self.birth_date:
            return None

        today = timezone.localdate()
        age = today.year - self.birth_date.year

        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1

        return age

    def __str__(self):
        return self.username or f"profile_{self.user_id}"


class ProfilePhoto(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="photos"
    )
    image = models.ImageField(
        upload_to="profile_photos/",
        validators=[validate_image_file]
    )
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_main", "-created_at"]

    def __str__(self):
        return f"Photo of {self.profile}"