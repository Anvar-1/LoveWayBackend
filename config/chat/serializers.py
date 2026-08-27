from rest_framework import serializers

from .models import (ChatRoom, Message, CallLog)


class UserShortSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    phone = serializers.CharField(read_only=True)
    username = serializers.SerializerMethodField()

    def get_username(self, obj):
        if hasattr(obj, "profile") and obj.profile:
            return obj.profile.username or obj.profile.full_name or obj.phone
        return getattr(obj, "phone", str(obj.id))


class ChatSerializer(serializers.ModelSerializer):

    user1 = UserShortSerializer(
        read_only=True
    )

    user2 = UserShortSerializer(
        read_only=True
    )

    class Meta:

        model = ChatRoom

        fields = ["id", "user1", "user2", "created_at", "updated_at"]


class MessageSerializer(serializers.ModelSerializer):

    sender = UserShortSerializer(
        read_only=True
    )

    class Meta:

        model = Message

        fields = ["id", "room", "sender", "text", "created_at"]


class CallLogSerializer(serializers.ModelSerializer):
    caller = UserShortSerializer(read_only=True)
    receiver = UserShortSerializer(read_only=True)

    class Meta:
        model = CallLog
        fields = [
            "id",
            "room",
            "caller",
            "receiver",
            "call_type",
            "status",
            "duration",
            "started_at",
            "ended_at",
        ]


class AgoraTokenRequestSerializer(serializers.Serializer):
    channel_name = serializers.CharField(max_length=100)
    uid = serializers.IntegerField(required=False, default=0)
    role = serializers.ChoiceField(choices=["publisher", "subscriber"], default="publisher")