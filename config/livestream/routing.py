from django.urls import re_path
from .consumers import LiveConsumer, LiveFeedConsumer

websocket_urlpatterns = [
    re_path(r"ws/live/(?P<live_id>[0-9a-f]+)/$", LiveConsumer.as_asgi()),
    re_path(r"ws/live-feed/$", LiveFeedConsumer.as_asgi()),
]
