from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from config.user.models import User
from config.profiles.models import Profile
from config.profiles.serializers import ProfileSerializer
from config.common.validators import validate_strong_password


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    gender = serializers.ChoiceField(
        choices=[("male", "Male"), ("female", "Female")],
        write_only=True,
    )

    def validate_password(self, value):
        return validate_strong_password(value)

    def validate_username(self, value):
        if Profile.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })
        return attrs

    def create(self, validated_data):
        phone = self.context["phone"]
        username = validated_data["username"]
        gender = validated_data["gender"]
        email = validated_data.get("email")

        user = User.objects.create_user(
            phone=phone,
            password=validated_data["password"],
            email=email if email else None,
            is_verified=True,
        )

        user.profile.username = username
        user.profile.gender = gender
        user.profile.save(update_fields=["username", "gender"])

        return user


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        phone = attrs.get("phone")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            phone=phone,
            password=password,
        )

        if not user:
            raise serializers.ValidationError("Invalid phone or password.")

        attrs["user"] = user
        return attrs


class MeSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "phone", "email", "is_verified", "profile"]


class AuthResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = MeSerializer(read_only=True)

    @staticmethod
    def build(user):
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": MeSerializer(user).data,
        }


class PasswordResetSendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        return validate_strong_password(value)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })
        return attrs