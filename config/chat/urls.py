from django.urls import path

from .views import (
    ChatCreateAPIView,
    ChatListAPIView,
    MessageCreateAPIView,
    MessageListAPIView,
    ICEServersAPIView,
    AgoraTokenAPIView,
    CallHistoryAPIView,
)


urlpatterns = [
    path("create/", ChatCreateAPIView.as_view()),
    path("list/", ChatListAPIView.as_view()),
    path("message/send/", MessageCreateAPIView.as_view()),
    path("<int:room_id>/messages/", MessageListAPIView.as_view()),
    path("call/ice-servers/", ICEServersAPIView.as_view()),
    path("call/agora-token/", AgoraTokenAPIView.as_view()),
    path("call/history/", CallHistoryAPIView.as_view()),
]