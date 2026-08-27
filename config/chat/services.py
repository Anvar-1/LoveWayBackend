from django.db.models import Q
from django.utils import timezone

from config.user.models import User

from .models import (
    ChatRoom,
    Message,
    MessageRead,
)



def get_or_create_chat(user1, user2):

    chat = ChatRoom.objects.filter(
        Q(user1=user1, user2=user2) |
        Q(user1=user2, user2=user1)
    ).first()


    if chat:
        return chat


    return ChatRoom.objects.create(
        user1=user1,
        user2=user2
    )



def get_user_chats(user):

    return ChatRoom.objects.filter(
        Q(user1=user) |
        Q(user2=user)
    )



def send_message(room, sender, text):

    message = Message.objects.create(
        room=room,
        sender=sender,
        text=text
    )


    room.updated_at = timezone.now()

    room.save(
        update_fields=[
            "updated_at"
        ]
    )


    return message



def get_messages(room):

    return Message.objects.filter(
        room=room,
        is_deleted=False
    )



def mark_messages_read(room, user):

    messages = Message.objects.filter(
        room=room
    ).exclude(
        sender=user
    )


    result = []


    for message in messages:

        read, created = MessageRead.objects.get_or_create(
            message=message,
            user=user
        )

        result.append(read)


    return result