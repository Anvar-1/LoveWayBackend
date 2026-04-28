from rest_framework import serializers
from .models import Friendship
from config.user.models import User


class FriendUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="profile.username", read_only=True)
    full_name = serializers.CharField(source="profile.full_name", read_only=True)
    avatar = serializers.ImageField(source="profile.avatar", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "avatar"]


class FriendshipSerializer(serializers.ModelSerializer):
    from_user = FriendUserSerializer(read_only=True)
    to_user = FriendUserSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = ["id", "from_user", "to_user", "status", "created_at", "updated_at"]


class SendFriendRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()


class RespondFriendRequestSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["accept", "reject"])