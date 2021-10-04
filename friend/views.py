from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import FriendRequest, FriendList
from .serializer import FriendRequestSerializer
from . import error_code


class InviteFriend(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, receiver):
        receiver = get_user_model().objects.get(pk=receiver)
        sender = request.user

        created = FriendRequest.invite(sender=sender, receiver=receiver).get('created')

        if created:
            return Response(status=201)
        return Response(status=200)


class AcceptFriend(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, sender):
        receiver = request.user
        sender = get_user_model().objects.get(pk=sender)
        if FriendRequest.objects.filter(sender=sender, receiver=receiver).exists():
            FriendRequest.objects.get(sender=sender, receiver=receiver).accept()

        return Response(status=200)


class RejectFriend(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, sender):

        sender = get_user_model().objects.get(pk=sender)
        receiver = request.user
        # try:
        #     FriendRequest.objects.get(sender=sender, receiver=receiver).decline()
        # except FriendRequest.DoesNotExist:
        #     return Response(status=200)
        if FriendRequest.objects.filter(sender=sender, receiver=receiver).exists():
            FriendRequest.objects.get(sender=sender, receiver=receiver).decline()

        return Response(status=200)


class CancelRequest(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, receiver):
        receiver = get_user_model().objects.get(pk=receiver)
        sender = request.user
        # try:
        #     FriendRequest.objects.get(sender=sender, receiver=receiver).decline()
        # except FriendRequest.DoesNotExist:
        #     return Response(status=200)
        if FriendRequest.objects.filter(sender=sender, receiver=receiver).exists():
            FriendRequest.objects.get(sender=sender, receiver=receiver).decline()

        return Response(status=200)


class RemoveFriend(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, friend):
        friend = get_user_model().objects.get(pk=friend)
        user = request.user

        user_friend_list = FriendList.objects.get(owner=user)

        user_friend_list.unfriend(friend)
        return Response(status=204)


class InvitesToMe(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        invites = FriendRequest.objects.filter(receiver=request.user)
        serializer = FriendRequestSerializer(invites, many=True, read_only=True)

        return Response(serializer.data)


# class InvitesFromMe(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         invites = FriendRequest.objects.filter(sender=request.user)
#         serializer = FriendRequestSerializer(invites, many=True, read_only=True)
#
#         return Response(serializer.data)
