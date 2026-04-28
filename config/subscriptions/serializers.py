from rest_framework import serializers
from .models import UserSubscription


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    plan_code = serializers.CharField(source="plan.code", read_only=True)

    class Meta:
        model = UserSubscription
        fields = ["id", "plan_name", "plan_code", "status", "starts_at", "ends_at", "auto_renew",]