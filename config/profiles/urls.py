from django.urls import path
from .views import MyProfileAPIView, MyProfilePhotoListCreateAPIView, MyProfilePhotoDeleteAPIView, \
    UpdateMyInterestsAPIView

urlpatterns = [
    path("me/", MyProfileAPIView.as_view(), name="my-profile"),
    path("photos/", MyProfilePhotoListCreateAPIView.as_view(), name="my-profile-photos"),
    path("photos/<int:pk>/delete/", MyProfilePhotoDeleteAPIView.as_view(), name="my-profile-photo-delete"),
    path("interests/", UpdateMyInterestsAPIView.as_view(), name="update-my-interests"),
]