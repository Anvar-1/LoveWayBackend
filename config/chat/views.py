from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from config.user.models import User

from .models import ChatRoom

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