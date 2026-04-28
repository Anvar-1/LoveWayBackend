from django.urls import path
from .views import InterestSearchAPIView, UserSearchAPIView

urlpatterns = [
    path("search/", InterestSearchAPIView.as_view(), name="interest-search"),
    path("interests/search/", InterestSearchAPIView.as_view(), name="interest-search"),
    path("users/search/", UserSearchAPIView.as_view(), name="user-search"),
]