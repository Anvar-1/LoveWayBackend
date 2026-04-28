from django.db import models

class OTPAttempt(models.Model):
    ACTION_CHOICES = (
        ("send", "Send"),
        ("verify", "Verify"),
        ("reset_send", "Reset Send"),
        ("reset_verify", "Reset Verify"),
    )

    phone = models.CharField(max_length=20)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    success = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone} - {self.action} - {self.success}"