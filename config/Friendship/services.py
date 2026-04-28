from django.db.models import Q
from rest_framework.exceptions import ValidationError, NotFound

from config.user.models import User
from .models import Friendship


class FriendshipService:
    @staticmethod
    def send_request(from_user, to_user_id: int):
        if from_user.id == to_user_id:
            raise ValidationError("You cannot send a friend request to yourself.")

        try:
            to_user = User.objects.get(id=to_user_id)
        except User.DoesNotExist:
            raise NotFound("User not found.")

        # Agar qarama-qarshi pending request bo‘lsa, auto accept qilamiz
        reverse_request = Friendship.objects.filter(
            from_user=to_user,
            to_user=from_user,
            status="pending"
        ).first()

        if reverse_request:
            reverse_request.status = "accepted"
            reverse_request.save(update_fields=["status", "updated_at"])
            return reverse_request, "accepted_existing"

        existing = Friendship.objects.filter(
            from_user=from_user,
            to_user=to_user
        ).first()

        if existing:
            if existing.status == "pending":
                raise ValidationError("Friend request already sent.")
            if existing.status == "accepted":
                raise ValidationError("You are already friends.")
            if existing.status == "rejected":
                existing.status = "pending"
                existing.save(update_fields=["status", "updated_at"])
                return existing, "resent"

        friendship = Friendship.objects.create(
            from_user=from_user,
            to_user=to_user,
            status="pending"
        )
        return friendship, "sent"

    @staticmethod
    def respond_to_request(user, friendship_id: int, action: str):
        try:
            friendship = Friendship.objects.get(id=friendship_id, to_user=user, status="pending")
        except Friendship.DoesNotExist:
            raise NotFound("Friend request not found.")

        if action == "accept":
            friendship.status = "accepted"
        elif action == "reject":
            friendship.status = "rejected"

        friendship.save(update_fields=["status", "updated_at"])
        return friendship

    @staticmethod
    def remove_friend(user, other_user_id: int):
        friendship = Friendship.objects.filter(
            (
                Q(from_user=user, to_user_id=other_user_id) |
                Q(from_user_id=other_user_id, to_user=user)
            ),
            status="accepted"
        ).first()

        if not friendship:
            raise NotFound("Friendship not found.")

        friendship.delete()
        return True

    @staticmethod
    def cancel_request(user, friendship_id: int):
        friendship = Friendship.objects.filter(
            id=friendship_id,
            from_user=user,
            status="pending"
        ).first()

        if not friendship:
            raise NotFound("Pending sent request not found.")

        friendship.delete()
        return True

    @staticmethod
    def get_friends(user):
        friendships = Friendship.objects.filter(
            Q(from_user=user, status="accepted") |
            Q(to_user=user, status="accepted")
        ).select_related(
            "from_user__profile",
            "to_user__profile"
        ).order_by("-updated_at")

        friends = []
        for item in friendships:
            friend = item.to_user if item.from_user_id == user.id else item.from_user
            friends.append(friend)

        return friends

    @staticmethod
    def get_incoming_requests(user):
        return Friendship.objects.filter(
            to_user=user,
            status="pending"
        ).select_related(
            "from_user__profile",
            "to_user__profile"
        ).order_by("-created_at")

    @staticmethod
    def get_sent_requests(user):
        return Friendship.objects.filter(
            from_user=user,
            status="pending"
        ).select_related(
            "from_user__profile",
            "to_user__profile"
        ).order_by("-created_at")