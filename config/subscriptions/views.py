from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSubscriptionSerializer
from .services import SubscriptionService, AccessPolicyService


class MySubscriptionAPIView(APIView):
    def get(self, request):
        subscription = SubscriptionService.get_current_subscription(request.user)
        if not subscription:
            return Response({"detail": "Hech qanday faol obuna topilmadi."}, status=404)

        return Response(UserSubscriptionSerializer(subscription).data)


class MyAccessAPIView(APIView):
    def get(self, request):
        current = SubscriptionService.get_current_subscription(request.user)
        permissions = AccessPolicyService.get_permissions(request.user)

        return Response({
            "state": permissions["state"],
            "trial_or_subscription_ends_at": current.ends_at if current else None,
            "permissions": permissions,
        })