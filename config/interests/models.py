from django.db import models

class Interest(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class UserInterest(models.Model):
    user = models.ForeignKey("user.User", on_delete=models.CASCADE, related_name="user_interests")
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE, related_name="user_interests")
    score = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "interest")

    def __str__(self):
        return f"{self.user.id} - {self.interest.name} ({self.score})"

class SearchHistory(models.Model):
    user = models.ForeignKey("user.User", on_delete=models.CASCADE, related_name="search_histories")
    query = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]