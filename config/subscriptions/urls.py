from django.urls import path
from .views import MySubscriptionAPIView, MyAccessAPIView

urlpatterns = [
    path("me/", MySubscriptionAPIView.as_view(), name="my-subscription"),
    path("access/", MyAccessAPIView.as_view(), name="my-access"),
]