from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser

from .serializers import (
    ChatSuggestSerializer,
    ProfilePhotoUploadSerializer,
    StoryVideoUploadSerializer,
)
from .services.chat_service import suggest_replies
from .services.moderation_service import moderate_image
from .services.video_service import moderate_video


class ChatSuggestAPIView(APIView):
    def post(self, request):
        serializer = ChatSuggestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            replies = suggest_replies(
                message=serializer.validated_data["message"],
                conversation=serializer.validated_data.get("conversation", []),
                tone=serializer.validated_data.get("tone", "friendly"),
            )
            return Response({"replies": replies}, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()

            return Response(
                {
                    "status": "error",
                    "message": "Javob variantlarini olishda xatolik yuz berdi.",
                    "detail": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ProfilePhotoModerateAPIView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = ProfilePhotoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            image = serializer.validated_data["image"]
            moderation = moderate_image(image)

            if moderation.get("sexual") or moderation.get("sexual_minors"):
                return Response(
                    {
                        "status": "rejected",
                        "reason": "adult_content",
                        "message": "Ushbu rasm platforma qoidalariga mos kelmadi."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {
                    "status": "approved",
                    "message": "Rasm qabul qilindi."
                },
                status=status.HTTP_200_OK
            )

        except Exception:
            return Response(
                {
                    "status": "error",
                    "message": "Rasmni tekshirishda xatolik yuz berdi."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StoryVideoModerateAPIView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = StoryVideoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            video = serializer.validated_data["video"]
            result = moderate_video(video)

            if result.get("status") == "rejected":
                return Response(
                    {
                        "status": "rejected",
                        "reason": "adult_content",
                        "message": "Story yuklanmadi. Nomaqbul kontent aniqlangan."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {
                    "status": "approved",
                    "message": "Story qabul qilindi."
                },
                status=status.HTTP_200_OK
            )

        except Exception:
            return Response(
                {
                    "status": "error",
                    "message": "Videoni tekshirishda xatolik yuz berdi."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )