from django.urls import path
from .views import (
    RegisterAPIView,
    LoginAPIView,
    MeAPIView,
    LogoutAPIView,
    SendOTPAPIView,
    VerifyOTPAPIView,
    PasswordResetSendOTPAPIView,
    PasswordResetConfirmAPIView,
)


urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("me/", MeAPIView.as_view(), name="me"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("otp/send/", SendOTPAPIView.as_view(), name="otp-send"),
    path("otp/verify/", VerifyOTPAPIView.as_view(), name="otp-verify"),
    path("password-reset/send-otp/", PasswordResetSendOTPAPIView.as_view(), name="password-reset-send-otp"),
    path("password-reset/confirm/", PasswordResetConfirmAPIView.as_view(), name="password-reset-confirm"),
]
