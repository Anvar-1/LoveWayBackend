from django.urls import path

from .views import (
    SendFriendRequestAPIView,
    RespondFriendRequestAPIView,
    CancelFriendRequestAPIView,
    RemoveFriendAPIView,
    FriendListAPIView,
    IncomingFriendRequestsAPIView,
    SentFriendRequestsAPIView,
)

urlpatterns = [
    path("request/send/", SendFriendRequestAPIView.as_view(), name="friend-request-send"),
    path("request/<int:pk>/respond/", RespondFriendRequestAPIView.as_view(), name="friend-request-respond"),
    path("request/<int:pk>/cancel/", CancelFriendRequestAPIView.as_view(), name="friend-request-cancel"),
    path("list/", FriendListAPIView.as_view(), name="friend-list"),
    path("requests/incoming/", IncomingFriendRequestsAPIView.as_view(), name="incoming-friend-requests"),
    path("requests/sent/", SentFriendRequestsAPIView.as_view(), name="sent-friend-requests"),
    path("remove/<int:user_id>/", RemoveFriendAPIView.as_view(), name="remove-friend"),
]