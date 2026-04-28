from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from .models import PrivacyPolicy, PrivacyPolicyAcceptance
from .serializers import PrivacyPolicySerializer, PrivacyPolicyAcceptanceSerializer
from config.common.utils import get_client_ip


class ActivePrivacyPolicyAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        policy = PrivacyPolicy.objects.filter(is_active=True).order_by("-published_at").first()
        if not policy:
            return Response({"detail": "Active privacy policy not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(PrivacyPolicySerializer(policy).data)


class AcceptPrivacyPolicyAPIView(APIView):
    def post(self, request):
        policy = PrivacyPolicy.objects.filter(is_active=True).order_by("-published_at").first()
        if not policy:
            return Response({"detail": "Active privacy policy not found."}, status=status.HTTP_404_NOT_FOUND)

        acceptance, created = PrivacyPolicyAcceptance.objects.get_or_create(
            user=request.user,
            policy=policy,
            defaults={
                "ip_address": get_client_ip(request),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            },
        )

        return Response(
            {
                "accepted": True,
                "created": created,
                "data": PrivacyPolicyAcceptanceSerializer(acceptance).data,
            },
            status=status.HTTP_200_OK,
        )


class MyPrivacyAcceptanceAPIView(APIView):
    def get(self, request):
        latest = PrivacyPolicyAcceptance.objects.filter(user=request.user).order_by("-accepted_at").first()
        if not latest:
            return Response({"accepted": False}, status=status.HTTP_200_OK)

        return Response({
            "accepted": True,
            "data": PrivacyPolicyAcceptanceSerializer(latest).data
        })