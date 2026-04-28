from django.conf import settings
from django.db import models


class SavedProfile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_profiles")
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_by_users")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "target_user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} saved {self.target_user}"
