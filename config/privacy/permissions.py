from rest_framework.permissions import BasePermission
from .models import PrivacyPolicy, PrivacyPolicyAcceptance


class HasAcceptedActivePrivacyPolicy(BasePermission):
    message = "You must accept the active privacy policy first."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        policy = PrivacyPolicy.objects.filter(is_active=True).order_by("-published_at").first()
        if not policy:
            return True

        return PrivacyPolicyAcceptance.objects.filter(
            user=request.user,
            policy=policy
        ).exists()