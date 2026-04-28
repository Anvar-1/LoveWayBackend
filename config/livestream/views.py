from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import (
    create_live_session,
    end_live_session,
    get_live_stats,
    get_live_viewers_with_profiles,
    get_live_comments,
)


class StartLiveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        title = request.data.get("title", "").strip()
        result = create_live_session(request.user.id, title=title)

        if not result["ok"]:
            return Response(result, status=400)

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "global_livestreams",
            {
                "type": "live.started",
                "payload": {
                    "live_id": result["live_id"],
                    "host_user_id": request.user.id,
                    "title": result.get("title", ""),
                    "started_at": result.get("started_at"),
                    "is_live": True,
                    "message": f"{request.user.username} streamga chiqdi",
                },
            },
        )

        return Response(result, status=201)


class EndLiveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, live_id):
        result = end_live_session(live_id, request.user.id)

        if result["ok"]:
            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                "global_livestreams",
                {
                    "type": "live.ended",
                    "payload": {
                        "live_id": live_id,
                        "host_user_id": request.user.id,
                        "is_live": False,
                        "message": f"{request.user.username} streamni tugatdi",
                    },
                },
            )

        status_code = 200 if result["ok"] else 400
        return Response(result, status=status_code)


class LiveStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, live_id):
        data = get_live_stats(live_id)
        if not data:
            return Response({"detail": "Live topilmadi."}, status=404)
        return Response(data, status=200)


class LiveViewersAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, live_id):
        data = get_live_viewers_with_profiles(live_id)
        return Response(data, status=200)


class LiveCommentsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, live_id):
        data = get_live_comments(live_id)
        return Response(data, status=200)