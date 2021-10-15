from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import FriendRequest, FriendList
from .serializer import FriendRequestSerializer
from . import error_code


class InviteFriend(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, receiver):
        receiver = get_object_or_404(get_user_model(), pk=receiver)
        sender = request.user

        created = FriendRequest.invite(sender=sender, receiver=receiver).get('created')

        if created:
            return Response(status=201)
        return Response(status=200)


class AcceptFriend(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, sender):
        receiver = request.user
        sender = get_object_or_404(get_user_model(), pk=sender)

        friend_request = get_object_or_404(FriendRequest, sender=sender, receiver=receiver)
        friend_request.accept()

        return Response(status=200)


class RejectFriend(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, sender):
        sender = get_object_or_404(get_user_model(), pk=sender)
        receiver = request.user

        friend_request = get_object_or_404(FriendRequest, sender=sender, receiver=receiver)
        friend_request.decline()

        return Response(status=204)


class CancelRequest(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, receiver):
        receiver = get_object_or_404(get_user_model(), pk=receiver)
        sender = request.user

        friend_request = get_object_or_404(FriendRequest, sender=sender, receiver=receiver)
        friend_request.decline()

        return Response(status=204)


class RemoveFriend(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, friend):
        friend = get_object_or_404(get_user_model(), pk=friend)
        user = request.user

        user_friend_list = FriendList.objects.get(owner=user)

        if not user_friend_list.is_friend(friend):
            return Response(error_code.IS_NOT_FRIEND, status=400)

        user_friend_list.unfriend(friend)
        return Response(status=204)


class InvitesToMe(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        invites = FriendRequest.objects.filter(receiver=request.user)
        serializer = FriendRequestSerializer(invites, many=True, read_only=True)

        return Response(serializer.data)
