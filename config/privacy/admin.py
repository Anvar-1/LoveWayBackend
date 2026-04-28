from django.contrib import admin
from .models import PrivacyPolicy, PrivacyPolicyAcceptance


@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "version", "is_active", "published_at")
    list_filter = ("is_active",)
    search_fields = ("title", "version")


@admin.register(PrivacyPolicyAcceptance)
class PrivacyPolicyAcceptanceAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "policy", "accepted_at", "ip_address")
    search_fields = ("user__phone", "policy__version", "ip_address")