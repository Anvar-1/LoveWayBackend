from django.urls import path
from .views import (StartLiveAPIView, EndLiveAPIView, LiveStatsAPIView, LiveViewersAPIView, LiveCommentsAPIView,)

urlpatterns = [
    path("start/", StartLiveAPIView.as_view(), name="live-start"),
    path("<str:live_id>/end/", EndLiveAPIView.as_view(), name="live-end"),
    path("<str:live_id>/stats/", LiveStatsAPIView.as_view(), name="live-stats"),
    path("<str:live_id>/viewers/", LiveViewersAPIView.as_view(), name="live-viewers"),
    path("<str:live_id>/comments/", LiveCommentsAPIView.as_view(), name="live-comments"),
]


# from django.urls import re_path
# from .consumers import LiveConsumer, LiveFeedConsumer
#
# websocket_urlpatterns = [
#     re_path(r"ws/live/(?P<live_id>[0-9a-f]+)/$", LiveConsumer.as_asgi()),
#     re_path(r"ws/live-feed/$", LiveFeedConsumer.as_asgi()),
# ]