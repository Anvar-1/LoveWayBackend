from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .services import get_story_viewers_with_profiles
from .services import (create_story, get_story, get_user_stories, delete_story, add_view, toggle_like, add_comment,
                       get_story_comments, get_story_viewers,)


class StoryCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get("file")
        media_type = request.data.get("media_type")
        caption = request.data.get("caption", "")

        if not file:
            return Response({"detail": "file required"}, status=400)

        if media_type not in ["photo", "video"]:
            return Response({"detail": "media_type photo/video bo‘lishi kerak"}, status=400)

        story = create_story(
            user_id=request.user.id,
            media_bytes=file.read(),
            media_type=media_type,
            caption=caption,
        )
        return Response(story, status=status.HTTP_201_CREATED)


class UserStoriesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        stories = get_user_stories(user_id)
        return Response(stories, status=200)


class StoryDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, story_id):
        result = delete_story(story_id, request.user)

        if not result["ok"]:
            if result["detail"] == "Permission denied":
                return Response(result, status=403)
            return Response(result, status=404)

        return Response(result, status=200)


class StoryDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, story_id):
        story = get_story(story_id)
        if not story:
            return Response({"detail": "Not found"}, status=404)
        return Response(story, status=200)


class StoryViewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, story_id):
        ok = add_view(story_id, request.user.id)
        if not ok:
            return Response({"detail": "Not found"}, status=404)
        return Response({"detail": "view added"}, status=200)


class StoryLikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, story_id):
        result = toggle_like(story_id, request.user.id)
        if not result["ok"]:
            return Response({"detail": result["detail"]}, status=404)
        return Response(result, status=200)


class StoryCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, story_id):
        text = request.data.get("text", "").strip()
        if not text:
            return Response({"detail": "text required"}, status=400)

        comment = add_comment(story_id, request.user.id, text)
        if not comment:
            return Response({"detail": "Not found"}, status=404)

        return Response(comment, status=201)

    def get(self, request, story_id):
        return Response(get_story_comments(story_id), status=200)



class StoryViewersAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, story_id):
        return Response(
            get_story_viewers_with_profiles(story_id),
            status=200,
        )