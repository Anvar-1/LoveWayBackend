from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from config.user.models import User
from .models import ChatRoom
from .services import send_message, get_or_create_chat
from .serializers import MessageSerializer


class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):

        self.user = self.scope.get("user")

        if not self.user or self.user.is_anonymous:
            print("CHAT WS REJECTED: Anonymous User")
            await self.accept()
            await self.send_json({"error": "Authentication required. Please provide a valid JWT token."})
            await self.close(code=4001)
            return

        self.raw_identifier = self.scope["url_route"]["kwargs"]["room_id"]

        room, err_msg = await self.get_or_resolve_room(self.raw_identifier, self.user)

        if not room or err_msg:
            print(f"CHAT WS REJECTED: User {self.user.id} identifier {self.raw_identifier} -> {err_msg}")
            await self.accept()
            await self.send_json({
                "error": err_msg,
                "detail": f"Identifier '{self.raw_identifier}' is neither an authorized ChatRoom ID nor a valid target User ID."
            })
            await self.close(code=4004)
            return

        self.room = room
        self.room_id = room.id
        self.room_group_name = f"chat_{room.id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.send_json({
            "status": "connected",
            "room_id": room.id,
            "user1_id": room.user1_id,
            "user2_id": room.user2_id,
            "message": f"Successfully connected to chat room {room.id} between user {room.user1_id} and user {room.user2_id}"
        })

        print(f"USER {self.user.id} CONNECTED TO CHAT ROOM {room.id} (Identifier: {self.raw_identifier})")

    async def disconnect(self, close_code):

        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive_json(self, content):

        if not isinstance(content, dict):
            await self.send_json({"error": "Invalid payload format. Must be a JSON object."})
            return

        text = content.get("message") or content.get("text")

        if not text or not str(text).strip():
            await self.send_json({"error": "Message text cannot be empty."})
            return

        message_data = await self.save_message(str(text).strip())

        if not message_data:
            await self.send_json({"error": "Failed to send message: chat room invalid or internal error occurred."})
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message_data
            }
        )

    async def chat_message(self, event):

        await self.send_json(
            event["message"]
        )

    @database_sync_to_async
    def get_or_resolve_room(self, identifier, user):
        try:
            identifier_id = int(identifier)
        except (ValueError, TypeError):
            return None, "Invalid ID format"

        # 1. Check if identifier is an existing ChatRoom ID
        try:
            room = ChatRoom.objects.get(id=identifier_id)
            if room.user1_id == user.id or room.user2_id == user.id:
                return room, None
            else:
                return None, f"You (User {user.id}) are not a participant in ChatRoom {identifier_id}"
        except ChatRoom.DoesNotExist:
            pass

        # 2. Check if identifier is a target User ID
        if identifier_id == user.id:
            return None, f"Cannot start a chat room with yourself (User ID {identifier_id}). Please specify target partner's User ID or the ChatRoom ID."

        try:
            target_user = User.objects.get(id=identifier_id)
            room = get_or_create_chat(user, target_user)
            return room, None
        except User.DoesNotExist:
            return None, f"No ChatRoom or User found with ID {identifier_id}"

    @database_sync_to_async
    def save_message(self, text):
        try:
            if not hasattr(self, "room") or not self.room:
                return None

            message = send_message(self.room, self.user, text)
            return MessageSerializer(message).data
        except Exception as e:
            print("SAVE MESSAGE ERROR:", e)
            return None