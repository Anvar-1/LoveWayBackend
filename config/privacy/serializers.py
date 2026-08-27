from rest_framework import serializers
from .models import PrivacyPolicy, PrivacyPolicyAcceptance, UserBlock


class PrivacyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = ["id", "version", "title", "content", "is_active", "published_at"]


class PrivacyPolicyAcceptanceSerializer(serializers.ModelSerializer):
    policy = PrivacyPolicySerializer(read_only=True)

    class Meta:
        model = PrivacyPolicyAcceptance
        fields = ["id", "policy", "accepted_at", "ip_address", "user_agent"]


class UserBlockActionSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()


class BlockedUserItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="blocked_user.id")
    phone = serializers.CharField(source="blocked_user.phone")
    username = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    blocked_at = serializers.DateTimeField(source="created_at")

    class Meta:
        model = UserBlock
        fields = ["id", "phone", "username", "full_name", "avatar", "blocked_at"]

    def get_username(self, obj):
        return getattr(getattr(obj.blocked_user, "profile", None), "username", None) or f"user_{obj.blocked_user_id}"

    def get_full_name(self, obj):
        return getattr(getattr(obj.blocked_user, "profile", None), "full_name", "")

    def get_avatar(self, obj):
        profile = getattr(obj.blocked_user, "profile", None)
        if profile and profile.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(profile.avatar.url)
            return profile.avatar.url
        return None