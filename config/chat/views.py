import time
from decouple import config
from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from agora_token_builder import RtcTokenBuilder

from config.user.models import User

from .models import ChatRoom, CallLog

from .services import (
    get_or_create_chat,
    get_user_chats,
    send_message,
    get_messages,
    mark_messages_read,
)

from .serializers import (
    ChatSerializer,
    MessageSerializer,
    CallLogSerializer,
    AgoraTokenRequestSerializer,
)


class ChatCreateAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        user_id = request.data.get(
            "user_id"
        )

        if not user_id:
            return Response(
                {"error": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid user_id format"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user_id == request.user.id:
            return Response(
                {"error": "Cannot create chat room with yourself"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target = User.objects.get(
                id=user_id
            )
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        chat = get_or_create_chat(
            request.user,
            target
        )

        return Response(
            ChatSerializer(chat).data,
            status=status.HTTP_200_OK
        )


class ChatListAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        chats = get_user_chats(
            request.user
        )

        return Response(
            ChatSerializer(
                chats,
                many=True
            ).data
        )


class MessageCreateAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        room_id = request.data.get(
            "room_id"
        )

        text = request.data.get(
            "text"
        )

        if not room_id or not text or not str(text).strip():
            return Response(
                {"error": "room_id and text are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            room = ChatRoom.objects.get(
                id=room_id
            )
        except ChatRoom.DoesNotExist:
            return Response(
                {"error": "Chat room not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if room.user1_id != request.user.id and room.user2_id != request.user.id:
            return Response(
                {"error": "You are not a participant in this chat room"},
                status=status.HTTP_403_FORBIDDEN
            )

        message = send_message(
            room,
            request.user,
            str(text).strip()
        )

        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED
        )


class MessageListAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request, room_id):

        try:
            room = ChatRoom.objects.get(
                id=room_id
            )
        except ChatRoom.DoesNotExist:
            return Response(
                {"error": "Chat room not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if room.user1_id != request.user.id and room.user2_id != request.user.id:
            return Response(
                {"error": "You are not a participant in this chat room"},
                status=status.HTTP_403_FORBIDDEN
            )

        mark_messages_read(
            room,
            request.user
        )

        messages = get_messages(
            room
        )

        return Response(
            MessageSerializer(
                messages,
                many=True
            ).data
        )


class ICEServersAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ice_servers = [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun1.l.google.com:19302"},
            {"urls": "stun:stun2.l.google.com:19302"},
            {"urls": "stun:stun3.l.google.com:19302"},
            {"urls": "stun:stun4.l.google.com:19302"},
        ]
        return Response({"ice_servers": ice_servers}, status=status.HTTP_200_OK)


class AgoraTokenAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AgoraTokenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        channel_name = serializer.validated_data["channel_name"]
        uid = serializer.validated_data.get("uid") or request.user.id
        role_str = serializer.validated_data.get("role", "publisher")

        app_id = config("AGORA_APP_ID", default="YOUR_AGORA_APP_ID")
        app_certificate = config("AGORA_APP_CERTIFICATE", default="YOUR_AGORA_APP_CERTIFICATE")

        role = 1 if role_str == "publisher" else 2
        expiration_time_in_seconds = 3600 * 24
        current_timestamp = int(time.time())
        privilege_expired_ts = current_timestamp + expiration_time_in_seconds

        try:
            token = RtcTokenBuilder.buildTokenWithUid(
                app_id, app_certificate, channel_name, uid, role, privilege_expired_ts
            )
        except Exception:
            token = f"token_{channel_name}_{uid}_{current_timestamp}"

        return Response(
            {
                "token": token,
                "app_id": app_id,
                "channel_name": channel_name,
                "uid": uid,
            },
            status=status.HTTP_200_OK,
        )


class CallHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        calls = CallLog.objects.filter(
            models.Q(caller=request.user) | models.Q(receiver=request.user)
        ).select_related("caller__profile", "receiver__profile", "room")[:50]

        return Response(CallLogSerializer(calls, many=True).data, status=status.HTTP_200_OK)