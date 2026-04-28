from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.accounts.services import delete_cached_user_session
from config.privacy.permissions import HasAcceptedActivePrivacyPolicy
from config.interests.models import Interest, UserInterest

from .models import ProfilePhoto
from .serializers import (
    ProfileSerializer,
    ProfilePhotoSerializer,
    ProfilePhotoCreateSerializer,
    UpdateMyInterestsSerializer,
)


class MyProfileAPIView(RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [HasAcceptedActivePrivacyPolicy]

    def get_object(self):
        return self.request.user.profile

    def perform_update(self, serializer):
        serializer.save()
        delete_cached_user_session(self.request.user.id)


class MyProfilePhotoListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.profile.photos.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProfilePhotoCreateSerializer
        return ProfilePhotoSerializer

    def perform_create(self, serializer):
        profile = self.request.user.profile
        is_main = serializer.validated_data.get("is_main", False)

        if is_main:
            profile.photos.update(is_main=False)

        serializer.save(profile=profile)


class MyProfilePhotoDeleteAPIView(DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfilePhotoSerializer

    def get_queryset(self):
        return self.request.user.profile.photos.all()

    def perform_destroy(self, instance):
        instance.delete()
        delete_cached_user_session(self.request.user.id)


class UpdateMyInterestsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UpdateMyInterestsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        interest_names = serializer.validated_data["interests"]
        user = request.user

        user.user_interests.all().delete()

        created_items = []
        for name in interest_names:
            cleaned = name.strip().lower()
            if not cleaned:
                continue

            interest, _ = Interest.objects.get_or_create(name=cleaned)
            UserInterest.objects.create(
                user=user,
                interest=interest,
                score=1,
            )
            created_items.append(interest.name)

        delete_cached_user_session(user.id)

        return Response(
            {"interests": created_items},
            status=status.HTTP_200_OK,
        )