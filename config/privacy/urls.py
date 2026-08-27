from django.urls import path
from .views import (
    ActivePrivacyPolicyAPIView,
    AcceptPrivacyPolicyAPIView,
    MyPrivacyAcceptanceAPIView,
    BlockUserAPIView,
    UnblockUserAPIView,
    BlockedUsersListAPIView,
)

urlpatterns = [
    path("active/", ActivePrivacyPolicyAPIView.as_view(), name="privacy-active"),
    path("accept/", AcceptPrivacyPolicyAPIView.as_view(), name="privacy-accept"),
    path("me/", MyPrivacyAcceptanceAPIView.as_view(), name="privacy-me"),
    path("block/", BlockUserAPIView.as_view(), name="block-user"),
    path("unblock/", UnblockUserAPIView.as_view(), name="unblock-user"),
    path("blocked-users/", BlockedUsersListAPIView.as_view(), name="blocked-users"),
]