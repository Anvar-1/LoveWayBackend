from django.http import HttpResponseForbidden
from django.conf import settings


class AdminIPRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_path = f"/{getattr(settings, 'ADMIN_URL', 'admin/')}".replace("//", "/")
        if request.path.startswith(admin_path):
            allowed_ips = getattr(settings, "ADMIN_ALLOWED_IPS", [])
            ip = request.META.get("REMOTE_ADDR")
            if allowed_ips and ip not in allowed_ips:
                return HttpResponseForbidden("Access denied.")
        return self.get_response(request)