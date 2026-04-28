from django.contrib import admin
from .models import Profile, ProfilePhoto


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "username",
        "full_name",
        "gender",
        "city",
        "district",
        "email",
        "marital_status",
        "has_children",
        "children_count",
    )
    search_fields = (
        "username",
        "full_name",
        "user__phone",
        "email",
        "city",
        "district",
    )


@admin.register(ProfilePhoto)
class ProfilePhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "is_main", "created_at")
    search_fields = ("profile__username", "profile__user__phone")