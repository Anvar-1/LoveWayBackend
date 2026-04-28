from random import randint

from django.utils import timezone
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from config.accounts.services import delete_cached_user_session

from config.user.models import User
from config.audit.services import create_audit_log
from config.common.utils import get_client_ip
from config.common.security import (
    increment_rate,
    block_key,
    enforce_block,
    set_otp,
    get_otp,
    delete_otp,
    set_reset_otp,
    get_reset_otp,
    delete_reset_otp,
    set_registration_session,
    get_registration_session,
    delete_registration_session,
)
from config.accounts.services import (
    cache_user_session,
    get_cached_user_session,
    delete_cached_user_session,
)
from .models import OTPAttempt
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    AuthResponseSerializer,
    MeSerializer,
    PasswordResetSendOTPSerializer,
    PasswordResetConfirmSerializer,
)


@method_decorator(ratelimit(key="ip", rate="7/10m", method="POST", block=True), name="dispatch")
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = get_registration_session(request)

        if not phone:
            return Response(
                {"detail": "Phone verification session expired or not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(phone=phone).exists():
            delete_registration_session(request)
            return Response(
                {"detail": "This phone is already registered."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RegisterSerializer(
            data=request.data,
            context={"phone": phone},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        delete_registration_session(request)
        cache_user_session(user)

        create_audit_log(
            user=user,
            action="register_success",
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            metadata={
                "phone": user.phone,
                "username": user.profile.username,
            },
        )

        return Response(
            AuthResponseSerializer.build(user),
            status=status.HTTP_201_CREATED,
        )


@method_decorator(ratelimit(key="ip", rate="5/10m", method="POST", block=True), name="dispatch")
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        cache_user_session(user)

        create_audit_log(
            user=user,
            action="login_success",
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            metadata={"phone": user.phone},
        )

        return Response(
            AuthResponseSerializer.build(user),
            status=status.HTTP_200_OK,
        )


class MeAPIView(APIView):
    def get(self, request):
        cached_data = get_cached_user_session(request.user.id)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        data = MeSerializer(request.user).data
        cache_user_session(request.user)

        return Response(data, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # 🔴 MUHIM: online statusni o‘chiramiz
        if hasattr(user, "profile"):
            user.profile.is_online = False
            user.profile.last_seen = timezone.now()
            user.profile.save(update_fields=["is_online", "last_seen"])

        # cache ni ham tozalaymiz
        delete_cached_user_session(user.id)

        return Response(
            {"detail": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )
class SendOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get("phone")
        ip = get_client_ip(request)

        if not phone:
            return Response(
                {"detail": "Phone is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        enforce_block(request, phone=phone)

        exceeded_ip, _ = increment_rate(f"otp:ip:{ip}", limit=5, ttl=600)
        exceeded_phone, _ = increment_rate(f"otp:phone:{phone}", limit=3, ttl=600)

        OTPAttempt.objects.create(
            phone=phone,
            ip_address=ip,
            action="send",
            success=not (exceeded_ip or exceeded_phone),
        )

        if exceeded_ip:
            block_key(f"block:ip:{ip}", ttl=3600)
            return Response(
                {"detail": "Too many OTP attempts from this IP."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if exceeded_phone:
            block_key(f"block:phone:{phone}", ttl=1800)
            return Response(
                {"detail": "Too many OTP requests for this phone."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        otp_code = str(randint(100000, 999999))
        set_otp(phone, otp_code, ttl=60)

        create_audit_log(
            action="otp_send_attempt",
            ip_address=ip,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            metadata={"phone": phone},
        )

        return Response(
            {
                "detail": "OTP sent successfully.",
                "otp": otp_code,  # faqat development uchun
            },
            status=status.HTTP_200_OK,
        )

class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get("phone")
        code = request.data.get("code")
        ip = get_client_ip(request)

        if not phone:
            return Response(
                {"detail": "Phone is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not code:
            return Response(
                {"detail": "OTP code is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        enforce_block(request, phone=phone)

        exceeded_verify, _ = increment_rate(f"otp-verify:ip:{ip}", limit=10, ttl=600)

        if exceeded_verify:
            OTPAttempt.objects.create(
                phone=phone,
                ip_address=ip,
                action="verify",
                success=False,
            )
            block_key(f"block:ip:{ip}", ttl=3600)
            return Response(
                {"detail": "Too many verification attempts."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        saved_code = get_otp(phone)

        if not saved_code:
            OTPAttempt.objects.create(
                phone=phone,
                ip_address=ip,
                action="verify",
                success=False,
            )

            create_audit_log(
                action="otp_verify_failed",
                ip_address=ip,
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                metadata={
                    "phone": phone,
                    "reason": "otp_not_found_or_expired",
                },
            )

            return Response(
                {"detail": "OTP expired or not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if str(saved_code) != str(code).strip():
            OTPAttempt.objects.create(
                phone=phone,
                ip_address=ip,
                action="verify",
                success=False,
            )

            create_audit_log(
                action="otp_verify_failed",
                ip_address=ip,
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                metadata={
                    "phone": phone,
                    "reason": "invalid_code",
                },
            )

            return Response(
                {"detail": "Invalid OTP code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        delete_otp(phone)
        set_registration_session(phone=phone, request=request, ttl=600)

        OTPAttempt.objects.create(
            phone=phone,
            ip_address=ip,
            action="verify",
            success=True,
        )

        create_audit_log(
            action="otp_verify_success",
            ip_address=ip,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            metadata={"phone": phone},
        )

        return Response(
            {"detail": "OTP verified. Continue registration."},
            status=status.HTTP_200_OK,
        )

class PasswordResetSendOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        ip = get_client_ip(request)

        enforce_block(request, phone=phone)

        exceeded_ip, _ = increment_rate(f"reset-otp:ip:{ip}", limit=5, ttl=600)
        exceeded_phone, _ = increment_rate(f"reset-otp:phone:{phone}", limit=3, ttl=600)

        OTPAttempt.objects.create(
            phone=phone,
            ip_address=ip,
            action="reset_send",
            success=not (exceeded_ip or exceeded_phone),
        )

        if exceeded_ip:
            block_key(f"block:ip:{ip}", ttl=3600)
            return Response(
                {"detail": "Too many reset OTP attempts from this IP."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if exceeded_phone:
            block_key(f"block:phone:{phone}", ttl=1800)
            return Response(
                {"detail": "Too many reset OTP requests for this phone."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        user = User.objects.filter(phone=phone).first()
        if not user:
            return Response(
                {"detail": "User with this phone was not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        otp_code = str(randint(100000, 999999))
        set_reset_otp(phone, otp_code, ttl=60)

        create_audit_log(
            user=user,
            action="password_reset_otp_sent",
            ip_address=ip,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            metadata={"phone": phone},
        )

        return Response(
            {
                "detail": "Password reset OTP sent successfully.",
                "otp": otp_code,  # faqat development uchun
            },
            status=status.HTTP_200_OK,
        )

class PasswordResetConfirmAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]
        password = serializer.validated_data["password"]
        ip = get_client_ip(request)

        enforce_block(request, phone=phone)

        exceeded_verify, _ = increment_rate(f"reset-otp-verify:ip:{ip}", limit=10, ttl=600)
        if exceeded_verify:
            OTPAttempt.objects.create(
                phone=phone,
                ip_address=ip,
                action="reset_verify",
                success=False,
            )
            block_key(f"block:ip:{ip}", ttl=3600)
            return Response(
                {"detail": "Too many password reset attempts."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        user = User.objects.filter(phone=phone).first()
        if not user:
            OTPAttempt.objects.create(
                phone=phone,
                ip_address=ip,
                action="reset_verify",
                success=False,
            )
            return Response(
                {"detail": "User with this phone was not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        saved_code = get_reset_otp(phone)
        if not saved_code:
            OTPAttempt.objects.create(
                phone=phone,
                ip_address=ip,
                action="reset_verify",
                success=False,
            )
            create_audit_log(
                user=user,
                action="password_reset_failed",
                ip_address=ip,
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                metadata={"phone": phone, "reason": "otp_not_found_or_expired"},
            )
            return Response(
                {"detail": "OTP expired or not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if str(saved_code) != str(code).strip():
            OTPAttempt.objects.create(
                phone=phone,
                ip_address=ip,
                action="reset_verify",
                success=False,
            )
            create_audit_log(
                user=user,
                action="password_reset_failed",
                ip_address=ip,
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                metadata={"phone": phone, "reason": "invalid_code"},
            )
            return Response(
                {"detail": "Invalid OTP code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password)
        user.save(update_fields=["password"])

        delete_reset_otp(phone)
        delete_cached_user_session(user.id)

        OTPAttempt.objects.create(
            phone=phone,
            ip_address=ip,
            action="reset_verify",
            success=True,
        )

        create_audit_log(
            user=user,
            action="password_reset_success",
            ip_address=ip,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            metadata={"phone": phone},
        )

        return Response(
            {"detail": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )