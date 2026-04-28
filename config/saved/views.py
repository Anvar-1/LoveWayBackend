from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import SaveProfileSerializer, SavedUserSerializer
from .services import SavedProfileService


class ToggleSaveProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SaveProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        is_saved = SavedProfileService.toggle_save(
            user=request.user,
            target_user_id=serializer.validated_data["user_id"]
        )

        return Response(
            {"saved": is_saved},
            status=status.HTTP_200_OK,
        )


class MySavedProfilesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = SavedProfileService.get_saved_profiles(request.user)

        return Response(
            SavedUserSerializer(users, many=True).data,
            status=status.HTTP_200_OK,
        )