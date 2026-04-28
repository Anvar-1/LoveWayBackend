from rest_framework.exceptions import ValidationError, NotFound
from config.user.models import User
from .models import SavedProfile


class SavedProfileService:

    @staticmethod
    def toggle_save(user, target_user_id):
        if user.id == target_user_id:
            raise ValidationError("You cannot save yourself.")

        try:
            target_user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            raise NotFound("User not found.")

        obj = SavedProfile.objects.filter(
            user=user,
            target_user=target_user
        ).first()

        if obj:
            obj.delete()
            return False  # saqlanmagan

        SavedProfile.objects.create(
            user=user,
            target_user=target_user
        )
        return True  # saqlangan

    @staticmethod
    def get_saved_profiles(user):
        return User.objects.filter(
            saved_by_users__user=user
        ).select_related("profile").order_by("-saved_by_users__created_at")