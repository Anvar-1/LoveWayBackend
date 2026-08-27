from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class ChatRoom(models.Model):

    user1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_created"
    )

    user2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_received"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )


    class Meta:
        unique_together = (
            "user1",
            "user2",
        )

        ordering = [
            "-updated_at"
        ]


    def __str__(self):
        return f"{self.user1} - {self.user2}"



class Message(models.Model):

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages"
    )


    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="messages_sent"
    )


    text = models.TextField()


    is_deleted = models.BooleanField(
        default=False
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:
        ordering = [
            "created_at"
        ]



    def __str__(self):
        return self.text



class MessageRead(models.Model):

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="reads"
    )


    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )


    read_at = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        unique_together = (
            "message",
            "user",
        )


class CallLog(models.Model):
    CALL_TYPE_CHOICES = (
        ("audio", "Audio Call"),
        ("video", "Video Call"),
    )
    STATUS_CHOICES = (
        ("missed", "Missed"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("ended", "Ended"),
        ("busy", "Busy"),
    )

    caller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="outgoing_calls",
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="incoming_calls",
    )
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="call_logs",
        null=True,
        blank=True,
    )
    call_type = models.CharField(max_length=10, choices=CALL_TYPE_CHOICES, default="audio")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="missed")
    duration = models.PositiveIntegerField(default=0)  # in seconds
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.call_type} call: {self.caller} -> {self.receiver} ({self.status})"