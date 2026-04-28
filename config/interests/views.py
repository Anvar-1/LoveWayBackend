from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from config.common.utils import get_client_ip
from config.profiles.serializers import ProfileSerializer
from .serializers import SearchSerializer
from .services import UserSearchService, InterestService
from .serializers import UserSearchResultSerializer


class InterestSearchAPIView(APIView):
    def post(self, request):
        serializer = SearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data["query"]
        ip = get_client_ip(request)

        InterestService.process_search(
            user=request.user,
            query=query,
            ip_address=ip,
        )

        profiles = InterestService.find_related_profiles(
            query=query,
            current_user=request.user,
        )

        return Response(
            {
                "query": query,
                "count": profiles.count() if hasattr(profiles, "count") else len(profiles),
                "results": ProfileSerializer(
                    profiles,
                    many=True,
                    context={"request": request}
                ).data,
            },
            status=status.HTTP_200_OK,
        )



class UserSearchAPIView(APIView):
    def get(self, request):
        query = request.query_params.get("q", "").strip()
        ip = get_client_ip(request)

        if query:
            if len(query) < 2:
                return Response([])

            users = UserSearchService.search(
                user=request.user,
                query=query,
            )

            # history + interest ni bir joyda yangilaymiz
            InterestService.process_search(
                user=request.user,
                query=query,
                ip_address=ip,
            )

        else:
            users = UserSearchService.suggest(request.user)

        serializer = UserSearchResultSerializer(
            users,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)