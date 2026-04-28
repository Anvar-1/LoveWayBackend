from django.utils import timezone
from rest_framework import serializers
from .models import Profile, ProfilePhoto
from .validators import validate_image_file


class ProfilePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilePhoto
        fields = ["id", "image", "is_main", "created_at"]


class ProfilePhotoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilePhoto
        fields = ["id", "image", "is_main"]

    def validate_image(self, value):
        validate_image_file(value)
        return value


class ProfileSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField(read_only=True)
    photos = ProfilePhotoSerializer(many=True, read_only=True)
    interests = serializers.SerializerMethodField(read_only=True)
    is_online = serializers.SerializerMethodField(read_only=True)
    online_status = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = ["id", "full_name", "username", "birth_date", "age", "gender", "bio", "city", "district",
            "email", "marital_status", "has_children", "children_count", "avatar", "photos", "interests",
            "is_online", "last_seen", "online_status", "created_at", "updated_at",]

        read_only_fields = ["id", "age", "photos", "interests", "is_online", "last_seen", "online_status", "created_at", "updated_at",]

    def get_age(self, obj):
        return obj.get_age()

    def get_interests(self, obj):
        return list(
            obj.user.user_interests
            .select_related("interest")
            .values_list("interest__name", flat=True)
        )

    def get_is_online(self, obj):
        if not obj.last_seen:
            return False
        return (timezone.now() - obj.last_seen).total_seconds() <= 120

    def get_online_status(self, obj):
        if not obj.last_seen:
            return "offline"

        diff = timezone.now() - obj.last_seen

        if diff.total_seconds() <= 120:
            return "online"
        if diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() // 60)
            return f"last seen {minutes} minute(s) ago"
        if diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() // 3600)
            return f"last seen {hours} hour(s) ago"

        days = diff.days
        return f"last seen {days} day(s) ago"

    def validate_username(self, value):
        value = (value or "").strip().lower()

        if not value:
            return value

        qs = Profile.objects.filter(username__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("This username is already taken.")

        return value

    def validate_email(self, value):
        value = (value or "").strip().lower()

        if not value:
            return value

        qs = Profile.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("This email is already taken.")

        return value

    def validate_avatar(self, value):
        validate_image_file(value)
        return value

    def validate_birth_date(self, value):
        if value is None:
            return value

        today = timezone.localdate()
        if value > today:
            raise serializers.ValidationError("Birth date cannot be in the future.")

        return value

    def validate(self, attrs):
        has_children = attrs.get(
            "has_children",
            getattr(self.instance, "has_children", False)
        )
        children_count = attrs.get(
            "children_count",
            getattr(self.instance, "children_count", 0)
        )

        if children_count < 0:
            raise serializers.ValidationError({
                "children_count": "Children count cannot be negative."
            })

        if not has_children and children_count > 0:
            raise serializers.ValidationError({
                "children_count": "If has_children is false, children_count must be 0."
            })

        if has_children and children_count < 1:
            raise serializers.ValidationError({
                "children_count": "Please provide children count."
            })

        return attrs


class UpdateMyInterestsSerializer(serializers.Serializer):
    interests = serializers.ListField(
        child=serializers.CharField(max_length=100),
        allow_empty=True
    )

    def validate_interests(self, value):
        cleaned = []
        seen = set()

        for item in value:
            name = item.strip().lower()
            if not name:
                continue

            if name not in seen:
                seen.add(name)
                cleaned.append(name)

        if len(cleaned) > 20:
            raise serializers.ValidationError("Siz 20 tagacha qiziqishni tanlashingiz mumkin.")

        return cleaned