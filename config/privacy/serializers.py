from rest_framework import serializers
from .models import PrivacyPolicy, PrivacyPolicyAcceptance


class PrivacyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = ["id", "version", "title", "content", "is_active", "published_at"]


class PrivacyPolicyAcceptanceSerializer(serializers.ModelSerializer):
    policy = PrivacyPolicySerializer(read_only=True)

    class Meta:
        model = PrivacyPolicyAcceptance
        fields = ["id", "policy", "accepted_at", "ip_address", "user_agent"]