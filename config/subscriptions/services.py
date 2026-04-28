from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from .models import SubscriptionPlan, UserSubscription


class SubscriptionService:
    @staticmethod
    def assign_trial(user):
        trial_plan, _ = SubscriptionPlan.objects.get_or_create(
            code="trial_30_days",
            defaults={
                "name": "30 Days Free Trial",
                "price": 0,
                "duration_days": 30,
                "is_trial": True,
                "is_active": True,
            },
        )

        now = timezone.now()

        return UserSubscription.objects.create(
            user=user,
            plan=trial_plan,
            status="trial",
            starts_at=now,
            ends_at=now + timedelta(days=trial_plan.duration_days),
            auto_renew=False,
        )

    @staticmethod
    def get_current_subscription(user):
        now = timezone.now()
        return user.subscriptions.filter(
            status__in=["trial", "active"],
            ends_at__gt=now,
        ).order_by("-created_at").first()


class AccessPolicyService:
    @staticmethod
    def get_state(user):
        current = SubscriptionService.get_current_subscription(user)
        if not current:
            return "limited"
        if current.status == "trial":
            return "trial"
        if current.status == "active":
            return "premium"
        return "limited"

    @staticmethod
    def get_permissions(user):
        state = AccessPolicyService.get_state(user)

        if state in ["trial", "premium"]:
            return {
                "state": state,
                "can_see_sender": True,
                "can_start_livestream": True,
                "can_post_story": True,
                "can_send_chat_icons": True,
                "can_read_messages": True,
                "can_receive_push": True,
            }

        return {
            "state": "limited",
            "can_see_sender": False,
            "can_start_livestream": False,
            "can_post_story": False,
            "can_send_chat_icons": False,
            "can_read_messages": True,
            "can_receive_push": True,
        }

    @staticmethod
    def require(user, permission_name):
        permissions = AccessPolicyService.get_permissions(user)
        if not permissions.get(permission_name, False):
            raise PermissionDenied("Premium required for this feature.")