from rest_framework import serializers

class ChatSuggestSerializer(serializers.Serializer):
    message = serializers.CharField()
    conversation = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )
    tone = serializers.ChoiceField(
        choices=["friendly", "serious", "funny"],
        required=False,
        default="friendly"
    )

class ProfilePhotoUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()


class StoryVideoUploadSerializer(serializers.Serializer):
    video = serializers.FileField()