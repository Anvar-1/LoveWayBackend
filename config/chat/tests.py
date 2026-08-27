from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from channels.testing import WebsocketCommunicator

from config.chat.models import ChatRoom, Message
from config.chat.consumers import ChatConsumer
from config.asgi import application

User = get_user_model()


class ChatAPITestCase(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(phone="+998901234567", password="password123")
        self.user2 = User.objects.create_user(phone="+998907654321", password="password123")
        self.user3 = User.objects.create_user(phone="+998900000000", password="password123")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

    def test_create_chat_success(self):
        response = self.client.post("/api/chat/create/", {"user_id": self.user2.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("id", response.data)

    def test_create_chat_with_self_fails(self):
        response = self.client.post("/api/chat/create/", {"user_id": self.user1.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_chat_nonexistent_user_fails(self):
        response = self.client.post("/api/chat/create/", {"user_id": 99999}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_send_and_get_messages(self):
        room = ChatRoom.objects.create(user1=self.user1, user2=self.user2)

        # Send message
        msg_resp = self.client.post("/api/chat/message/create/", {"room_id": room.id, "text": "Hello world!"}, format="json")
        self.assertEqual(msg_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(msg_resp.data["text"], "Hello world!")

        # Get messages
        get_resp = self.client.get(f"/api/chat/messages/{room.id}/")
        self.assertEqual(get_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_resp.data), 1)

    def test_unauthorized_room_access_fails(self):
        room = ChatRoom.objects.create(user1=self.user2, user2=self.user3)

        # user1 trying to access room between user2 and user3
        get_resp = self.client.get(f"/api/chat/messages/{room.id}/")
        self.assertEqual(get_resp.status_code, status.HTTP_403_FORBIDDEN)


class ChatWebSocketTestCase(TestCase):

    async def test_websocket_connect_by_target_user_id(self):
        user1 = await User.objects.acreate_user(phone="+998911111111", password="password123")
        user2 = await User.objects.acreate_user(phone="+998922222222", password="password123")

        # Connect user1 to /ws/chat/<user2.id>/
        communicator = WebsocketCommunicator(application, f"/ws/chat/{user2.id}/")
        communicator.scope["user"] = user1

        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)

        response = await communicator.receive_json_from()
        self.assertEqual(response.get("status"), "connected")
        await communicator.disconnect()

    async def test_websocket_connect_nonexistent_room_and_user(self):
        user = await User.objects.acreate_user(phone="+998933333333", password="password123")
        communicator = WebsocketCommunicator(application, "/ws/chat/99999/")
        communicator.scope["user"] = user

        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)

        response = await communicator.receive_json_from()
        self.assertIn("error", response)
        await communicator.disconnect()
