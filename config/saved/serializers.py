from rest_framework import serializers
from config.user.models import User


class SaveProfileSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()


class SavedUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="profile.username")
    full_name = serializers.CharField(source="profile.full_name")
    avatar = serializers.ImageField(source="profile.avatar")

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "avatar"]