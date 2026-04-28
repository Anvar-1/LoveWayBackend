from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "config.profiles"

    def ready(self):
        import config.profiles.signals  # noqa
