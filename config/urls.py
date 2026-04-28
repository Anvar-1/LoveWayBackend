from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),

    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/auth/", include("config.accounts.urls")),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("profile/", include("config.profiles.urls")),
    path("sub/", include("config.subscriptions.urls")),
    path("privacy/", include("config.privacy.urls")),
    path("interests/", include("config.interests.urls")),
    path("friends/", include("config.Friendship.urls")),
    path("saved/", include("config.saved.urls")),
    path("stories/", include("config.stories.urls")),
    path("live/", include("config.livestream.urls")),
    path("api/ai/", include("config.ai.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)