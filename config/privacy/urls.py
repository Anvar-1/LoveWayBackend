from django.urls import path
from .views import ActivePrivacyPolicyAPIView, AcceptPrivacyPolicyAPIView, MyPrivacyAcceptanceAPIView

urlpatterns = [
    path("active/", ActivePrivacyPolicyAPIView.as_view(), name="privacy-active"),
    path("accept/", AcceptPrivacyPolicyAPIView.as_view(), name="privacy-accept"),
    path("me/", MyPrivacyAcceptanceAPIView.as_view(), name="privacy-me"),
]