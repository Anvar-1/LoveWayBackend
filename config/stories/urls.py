from django.urls import path
from .views import (StoryCreateAPIView, StoryDeleteAPIView, UserStoriesAPIView, StoryDetailAPIView, StoryViewAPIView,
    StoryLikeAPIView, StoryCommentAPIView, StoryViewersAPIView,)

urlpatterns = [
    path("", StoryCreateAPIView.as_view()),
    path("user/<int:user_id>/", UserStoriesAPIView.as_view()),
    path("<str:story_id>/delete/", StoryDeleteAPIView.as_view()),
    path("<str:story_id>/", StoryDetailAPIView.as_view()),
    path("<str:story_id>/view/", StoryViewAPIView.as_view()),
    path("<str:story_id>/like/", StoryLikeAPIView.as_view()),
    path("<str:story_id>/comment/", StoryCommentAPIView.as_view()),
    path("<str:story_id>/viewers/", StoryViewersAPIView.as_view()),
]