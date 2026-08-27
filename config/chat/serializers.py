from rest_framework import serializers

from .models import (ChatRoom, Message)


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