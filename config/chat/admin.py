from django.contrib import admin

from .models import (
    ChatRoom,
    Message,
    MessageRead,
)


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user1",
        "user2",
        "created_at",
        "updated_at",
    )



@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "room",
        "sender",
        "text",
        "created_at",
    )

    search_fields = (
        "text",
    )



@admin.register(MessageRead)
class MessageReadAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "message",
        "user",
        "read_at",
    )