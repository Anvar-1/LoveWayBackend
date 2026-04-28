from django.core.management.base import BaseCommand
from config.privacy.models import PrivacyPolicy


class Command(BaseCommand):
    help = "Seed default privacy policy"

    def handle(self, *args, **kwargs):
        policy, created = PrivacyPolicy.objects.get_or_create(
            version="1.0",
            defaults={
                "title": "Privacy Policy",
                "content": "Default policy",
                "is_active": True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS("Privacy policy created"))
        else:
            self.stdout.write(self.style.WARNING("Privacy policy already exists"))