from django.db.models.signals import post_save
from django.dispatch import receiver
from config.subscriptions.services import SubscriptionService
from config.user.models import User
from config.profiles.models import Profile


@receiver(post_save, sender=User)
def create_profile_and_trial(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
            user=instance,
            full_name=""
        )
        SubscriptionService.assign_trial(instance)