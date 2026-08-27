from urllib.parse import parse_qs

from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.db import close_old_connections


class JWTAuthMiddleware(BaseMiddleware):

    async def __call__(self, scope, receive, send):

        close_old_connections()

        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)

        token = None

        if "token" in query_params:
            token = query_params["token"][0]
        else:
            headers = dict(scope.get("headers", []))
            if b"authorization" in headers:
                auth_header = headers[b"authorization"].decode()
                if auth_header.lower().startswith("bearer "):
                    token = auth_header.split(" ", 1)[1]

        if token:
            jwt_auth = JWTAuthentication()
            try:
                if token.lower().startswith("bearer "):
                    token = token.split(" ", 1)[1]

                validated_token = jwt_auth.get_validated_token(token)
                user = await self.get_user(validated_token)
                scope["user"] = user
            except Exception as e:
                print("JWT AUTH ERROR:", e)
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(
            scope,
            receive,
            send
        )

    @staticmethod
    async def get_user(token):

        from config.user.models import User

        user_id = token.get("user_id")
        if not user_id:
            return AnonymousUser()

        try:
            return await User.objects.aget(id=user_id)
        except Exception:
            return AnonymousUser()