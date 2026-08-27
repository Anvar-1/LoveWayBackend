from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from config.common.utils import get_client_ip
from .models import Interest
from .services import UserSearchService, InterestService
from .serializers import UserSearchResultSerializer, InterestModelSerializer
from ..user.models import User


class UserSearchAPIView(APIView):
    """Foydalanuvchilarni qidirish va ularning qiziqishlarini ham qaytarish"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '')
        # Qidiruv tarixini saqlash va ballash
        InterestService.process_search_query(request.user, query)

        # Foydalanuvchilarni qidirish
        users = UserSearchService.search(request.user, query)

        # Serializer orqali qiziqishlari bilan birga qaytarish
        serializer = UserSearchResultSerializer(users, many=True)
        return Response(serializer.data)


class InterestSearchAPIView(APIView):
    """Foydalanuvchi qiziqish qo'shayotganda tizimdagi bor qiziqishlarni qidirishi uchun"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        interests = Interest.objects.filter(name__icontains=query)[:10]
        serializer = InterestModelSerializer(interests, many=True)
        return Response(serializer.data)

class ProfileDetailAPIView(APIView):
    """Foydalanuvchi profiliga kirganda ballni oshirish uchun namuna"""

    def get(self, request, pk):
        profile_user = User.objects.get(pk=pk)

        # Click ballini oshirish (Redis kesh avtomatik o'chadi)
        InterestService.boost_interest_on_click(request.user, profile_user)

        # ... qolgan mantiq (profil ma'lumotlarini qaytarish) ...
        return Response({"status": "ok"})