from django.db import transaction
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from config.user.models import User
from config.Friendship.models import Friendship
from .models import UserBlock


def block_user(user: User, blocked_user_id: int) -> UserBlock:
    if user.id == int(blocked_user_id):
        raise ValidationError({"detail": "You cannot block yourself."})

    try:
        target_user = User.objects.get(pk=blocked_user_id)
    except User.DoesNotExist:
        raise ValidationError({"detail": "User to block was not found."})

    with transaction.atomic():
        block_obj, created = UserBlock.objects.get_or_create(
            user=user,
            blocked_user=target_user,
        )

        # Do'stlik munosabati bo'lsa, uni o'chirib tashlaymiz
        Friendship.objects.filter(
            (Q(from_user=user) & Q(to_user=target_user)) |
            (Q(from_user=target_user) & Q(to_user=user))
        ).delete()

    return block_obj


def unblock_user(user: User, blocked_user_id: int) -> bool:
    if user.id == int(blocked_user_id):
        raise ValidationError({"detail": "You cannot unblock yourself."})

    deleted_count, _ = UserBlock.objects.filter(
        user=user,
        blocked_user_id=blocked_user_id,
    ).delete()

    return deleted_count > 0


def is_blocked_between(user1_id: int, user2_id: int) -> bool:
    if not user1_id or not user2_id:
        return False
    return UserBlock.objects.filter(
        (Q(user_id=user1_id) & Q(blocked_user_id=user2_id)) |
        (Q(user_id=user2_id) & Q(blocked_user_id=user1_id))
    ).exists()
