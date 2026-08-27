from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from .models import PrivacyPolicy, PrivacyPolicyAcceptance, UserBlock
from .serializers import (
    PrivacyPolicySerializer,
    PrivacyPolicyAcceptanceSerializer,
    UserBlockActionSerializer,
    BlockedUserItemSerializer,
)
from .services import block_user, unblock_user
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


class BlockUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserBlockActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_user_id = serializer.validated_data["user_id"]
        block_obj = block_user(request.user, target_user_id)

        return Response(
            {
                "detail": f"User {target_user_id} has been blocked successfully.",
                "blocked_user_id": target_user_id,
            },
            status=status.HTTP_200_OK,
        )


class UnblockUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserBlockActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_user_id = serializer.validated_data["user_id"]
        unblocked = unblock_user(request.user, target_user_id)

        if not unblocked:
            return Response(
                {"detail": "User was not in your block list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": f"User {target_user_id} has been unblocked successfully.",
                "unblocked_user_id": target_user_id,
            },
            status=status.HTTP_200_OK,
        )


class BlockedUsersListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        blocked_qs = UserBlock.objects.filter(user=request.user).select_related("blocked_user__profile")
        serializer = BlockedUserItemSerializer(blocked_qs, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)