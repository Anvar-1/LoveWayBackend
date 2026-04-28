from django.urls import path
from .views import (
    ChatSuggestAPIView,
    ProfilePhotoModerateAPIView,
    StoryVideoModerateAPIView,
)

urlpatterns = [
    path("chat-suggest/", ChatSuggestAPIView.as_view(), name="chat-suggest"),
    path("profile-photo-check/", ProfilePhotoModerateAPIView.as_view(), name="profile-photo-check"),
    path("story-video-check/", StoryVideoModerateAPIView.as_view(), name="story-video-check"),
]
