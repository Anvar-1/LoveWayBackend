from django.urls import path
from .views import ToggleSaveProfileAPIView, MySavedProfilesAPIView

urlpatterns = [
    path("toggle/", ToggleSaveProfileAPIView.as_view(), name="toggle-save-profile"),
    path("me/", MySavedProfilesAPIView.as_view(), name="my-saved-profiles"),
]