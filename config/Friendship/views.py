from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import (SendFriendRequestSerializer, RespondFriendRequestSerializer, FriendshipSerializer,
    FriendUserSerializer,)
from .services import FriendshipService


class SendFriendRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendFriendRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        friendship, result = FriendshipService.send_request(
            from_user=request.user,
            to_user_id=serializer.validated_data["user_id"],
        )

        return Response(
            {
                "result": result,
                "data": FriendshipSerializer(friendship).data,
            },
            status=status.HTTP_200_OK,
        )


class RespondFriendRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = RespondFriendRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        friendship = FriendshipService.respond_to_request(
            user=request.user,
            friendship_id=pk,
            action=serializer.validated_data["action"],
        )

        return Response(
            FriendshipSerializer(friendship).data,
            status=status.HTTP_200_OK,
        )


class CancelFriendRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        FriendshipService.cancel_request(
            user=request.user,
            friendship_id=pk,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class RemoveFriendAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        FriendshipService.remove_friend(
            user=request.user,
            other_user_id=user_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class FriendListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        friends = FriendshipService.get_friends(request.user)
        return Response(
            FriendUserSerializer(friends, many=True, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class IncomingFriendRequestsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests_qs = FriendshipService.get_incoming_requests(request.user)
        return Response(
            FriendshipSerializer(requests_qs, many=True, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class SentFriendRequestsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests_qs = FriendshipService.get_sent_requests(request.user)
        return Response(
            FriendshipSerializer(requests_qs, many=True, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )
