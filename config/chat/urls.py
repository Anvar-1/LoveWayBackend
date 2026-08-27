from django.urls import path

from .views import (ChatCreateAPIView, ChatListAPIView, MessageCreateAPIView,
    MessageListAPIView,)


urlpatterns = [
    path("create/", ChatCreateAPIView.as_view()),
    path("list/", ChatListAPIView.as_view()),
    path("message/send/", MessageCreateAPIView.as_view()),
    path("<int:room_id>/messages/", MessageListAPIView.as_view()),

]