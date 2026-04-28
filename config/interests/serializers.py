from config.user.models import User
from rest_framework import serializers


class SearchSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=255)



class UserSearchResultSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="profile.username", read_only=True)
    full_name = serializers.CharField(source="profile.full_name", read_only=True)
    bio = serializers.CharField(source="profile.bio", read_only=True)
    city = serializers.CharField(source="profile.city", read_only=True)
    country = serializers.CharField(source="profile.country", read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "full_name",
            "bio",
            "city",
            "country",
            "avatar",
        ]

    def get_avatar(self, obj):
        request = self.context.get("request")
        avatar = getattr(obj.profile, "avatar", None)

        if avatar:
            try:
                return request.build_absolute_uri(avatar.url) if request else avatar.url
            except Exception:
                return None
        return None