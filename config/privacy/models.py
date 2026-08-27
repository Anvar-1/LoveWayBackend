from django.db import models


class PrivacyPolicy(models.Model):
    version = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255, default="Privacy Policy")
    content = models.TextField()
    is_active = models.BooleanField(default=False)
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return f"{self.title} - {self.version}"


class PrivacyPolicyAcceptance(models.Model):
    user = models.ForeignKey("user.User", on_delete=models.CASCADE, related_name="privacy_acceptances")
    policy = models.ForeignKey(PrivacyPolicy, on_delete=models.CASCADE, related_name="acceptances")
    accepted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        unique_together = ("user", "policy")

    def __str__(self):
        return f"{self.user} accepted {self.policy.version}"


class UserBlock(models.Model):
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="blocked_users",
    )
    blocked_user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="blocked_by_users",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "blocked_user"],
                name="unique_user_block",
            )
        ]

    def __str__(self):
        return f"User {self.user_id} blocked User {self.blocked_user_id}"