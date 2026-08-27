from rest_framework import serializers
from config.user.models import User
from .models import Interest, UserInterest

class InterestModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'name']

class UserInterestDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='interest.name')
    class Meta:
        model = UserInterest
        fields = ['name', 'score']

class UserSearchResultSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='profile.full_name')
    username = serializers.CharField(source='profile.username')
    # Foydalanuvchining o'z qiziqishlarini chiqarish
    user_interests = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'user_interests']

    def get_user_interests(self, obj):
        interests = UserInterest.objects.filter(user=obj).select_related('interest').order_by('-score')[:5]
        return UserInterestDetailSerializer(interests, many=True).data