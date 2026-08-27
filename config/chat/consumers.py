from django.utils import timezone
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from config.user.models import User
from config.privacy.services import is_blocked_between
from .models import ChatRoom, CallLog
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

        action = content.get("action") or content.get("type")

        # ----------------------------------------------------
        # Real-time WebRTC Call Signaling Actions
        # ----------------------------------------------------
        if action in ["call_offer", "call_answer", "ice_candidate", "call_reject", "call_end"]:
            await self.handle_call_signal(action, content)
            return

        # ----------------------------------------------------
        # Regular Chat Message
        # ----------------------------------------------------
        text = content.get("message") or content.get("text")

        if not text or not str(text).strip():
            await self.send_json({"error": "Message text or valid call action cannot be empty."})
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

    async def call_signal(self, event):

        await self.send_json(event)

    async def handle_call_signal(self, action, content):

        partner_id = self.room.user2_id if self.user.id == self.room.user1_id else self.room.user1_id

        # Check if users have blocked each other
        blocked = await database_sync_to_async(is_blocked_between)(self.user.id, partner_id)
        if blocked and action == "call_offer":
            await self.send_json({
                "action": "call_rejected",
                "reason": "user_blocked",
                "detail": "Cannot place call because user is blocked."
            })
            return

        if action == "call_offer":
            call_type = content.get("call_type", "audio")
            call_log = await self.create_call_log(self.user.id, partner_id, self.room.id, call_type)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "call_signal",
                    "action": "call_offer",
                    "caller_id": self.user.id,
                    "caller_phone": self.user.phone,
                    "call_type": call_type,
                    "sdp": content.get("sdp"),
                    "call_id": call_log.id if call_log else None,
                    "room_id": self.room_id,
                }
            )

        elif action == "call_answer":
            call_id = content.get("call_id")
            if call_id:
                await self.update_call_log_status(call_id, "accepted")

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "call_signal",
                    "action": "call_answer",
                    "user_id": self.user.id,
                    "call_id": call_id,
                    "sdp": content.get("sdp"),
                }
            )

        elif action == "ice_candidate":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "call_signal",
                    "action": "ice_candidate",
                    "user_id": self.user.id,
                    "candidate": content.get("candidate"),
                }
            )

        elif action == "call_reject":
            call_id = content.get("call_id")
            if call_id:
                await self.update_call_log_status(call_id, "rejected")

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "call_signal",
                    "action": "call_rejected",
                    "user_id": self.user.id,
                    "call_id": call_id,
                }
            )

        elif action == "call_end":
            call_id = content.get("call_id")
            duration = int(content.get("duration", 0))
            if call_id:
                await self.update_call_log_status(call_id, "ended", duration=duration)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "call_signal",
                    "action": "call_ended",
                    "user_id": self.user.id,
                    "call_id": call_id,
                    "duration": duration,
                }
            )

    @database_sync_to_async
    def create_call_log(self, caller_id, receiver_id, room_id, call_type):
        try:
            return CallLog.objects.create(
                caller_id=caller_id,
                receiver_id=receiver_id,
                room_id=room_id,
                call_type=call_type,
                status="missed",
            )
        except Exception as e:
            print("CREATE CALL LOG ERROR:", e)
            return None

    @database_sync_to_async
    def update_call_log_status(self, call_id, status, duration=0):
        try:
            call_log = CallLog.objects.filter(id=call_id).first()
            if call_log:
                call_log.status = status
                if duration > 0:
                    call_log.duration = duration
                if status in ["ended", "rejected"]:
                    call_log.ended_at = timezone.now()
                call_log.save()
        except Exception as e:
            print("UPDATE CALL LOG ERROR:", e)

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