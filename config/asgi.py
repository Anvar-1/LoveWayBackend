import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

import django
django.setup()


from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter

from config.chat.middleware import JWTAuthMiddleware
from config.chat.routing import websocket_urlpatterns as chat_urlpatterns
from config.livestream.routing import websocket_urlpatterns as live_urlpatterns


django_asgi_app = get_asgi_application()



application = ProtocolTypeRouter({

    "http": django_asgi_app,


    "websocket": JWTAuthMiddleware(
        URLRouter(
            chat_urlpatterns + live_urlpatterns
        )
    ),

})