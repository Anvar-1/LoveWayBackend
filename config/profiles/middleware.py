from django.utils import timezone


class UpdateLastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            profile = getattr(user, "profile", None)
            if profile:
                profile.last_seen = timezone.now()
                profile.is_online = True
                profile.save(update_fields=["last_seen", "is_online"])

        return response