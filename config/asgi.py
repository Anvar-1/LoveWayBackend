import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from config.livestream.middleware import QueryStringJWTAuthMiddleware
import config.livestream.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": QueryStringJWTAuthMiddleware(
        URLRouter(config.livestream.routing.websocket_urlpatterns)
    ),
})