from django.contrib.auth import get_user_model
from django.db.models import Value
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from Messenger.general_functions import validate_offset_and_limit
from . import error_code
from .models import ChatRoom, Message, ChatroomInvitation
from .serializer import GroupSerializer, MessageSerializer, ChatRoomInvitationSerializer, ChatroomUserSerializer


class GetUserChatRoom(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        groups = ChatRoom.get_group_by_user(user=user)
        serializer = GroupSerializer(groups, many=True, context={'request': request})
        return Response(serializer.data)


class GetChatRoomMessages(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_pk):
        room_name = room_pk

        group = ChatRoom.objects.get(pk=room_name)

        if request.user not in group.users.all():
            return Response(status=401)

        offset, limit = validate_offset_and_limit(request)

        if request.GET.get('last_message') is not None:
            try:
                last_message = int(request.GET.get('last_message'))
            except ValueError:
                return Response(error_code.LAST_MESSAGE_INT, status=400)

            if not Message.objects.filter(pk=last_message).exists():
                return Response(error_code.NO_LAST_MESSAGE, status=400)

            last_message = Message.objects.get(pk=last_message)
            qs = group.messages.filter(created_at__gte=last_message.created_at)[offset:limit]
        else:
            qs = group.messages.all()[offset:limit]

        serializer = MessageSerializer(qs,
                                       many=True,
                                       read_only=True,
                                       context={'request': request})

        return Response(serializer.data)


class GetChatRoomInfo(APIView):
    def get(self, request, chat_room_pk):
        chat_room = get_object_or_404(ChatRoom, pk=chat_room_pk)
        serializer = GroupSerializer(chat_room, context={'request': request})
        return Response(serializer.data)


class CreateRoom(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get('name')

        if name is None or not name:
            return Response(error_code.NO_CHATROOM_NAME, status=400)

        if ChatRoom.objects.filter(name=name).exists():
            return Response(error_code.CHATROOM_ALREADY_EXISTS, status=400)

        chat_room = ChatRoom.objects.create(name=name)
        chat_room.users.add(request.user)
        chat_room.creators.add(request.user)

        serializer = GroupSerializer(chat_room)

        return Response(serializer.data, status=201)


class InvitesToMe(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        invitations = request.user.chatroom_invitations.all()
        serializer = ChatRoomInvitationSerializer(invitations, many=True, read_only=True, context={'request': request})

        return serializer.data


class InviteUser(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chatroom_pk):
        chatroom = get_object_or_404(ChatRoom, pk=chatroom_pk)

        if request.user not in chatroom.creators.all():
            return Response(error_code.USER_NOT_ADMIN, status=403)

        if request.data.get('user') is None:
            return Response(error_code.USER_IS_NONE)

        receiver = get_user_model().objects.get(pk=request.data.get('user'))

        if receiver == request.user:
            return Response(error_code.CANT_INVITE_YOURSELF, status=400)

        if ChatroomInvitation.objects.filter(receiver=receiver, chatroom=chatroom).exists():
            return Response(error_code.SAME_INVITATION_EXISTS, status=400)

        if request.data.get('user') in chatroom.users.all():
            return Response(error_code.USER_IS_MEMBER, status=400)

        ChatroomInvitation.objects.create(sender=request.user, receiver=receiver, chatroom=chatroom)

        return Response(status=201)


class CancelRequest(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chatroom_pk):
        chatroom = get_object_or_404(ChatRoom, pk=chatroom_pk)

        if request.user not in chatroom.creators.all():
            return Response(error_code.USER_NOT_ADMIN, status=403)

        if request.data.get('user') is None:
            return Response(error_code.USER_IS_NONE, status=400)

        if not get_user_model().objects.filter(pk=request.data.get('user')).exists():
            return Response(error_code.NO_USER_WITH_PK, status=400)

        receiver = get_user_model().objects.get(pk=request.data.get('user'))

        if not ChatroomInvitation.objects.filter(receiver=receiver, chatroom=chatroom).exists():
            return Response(error_code.INVITATION_DOESNT_EXISTS, status=400)

        if request.data.get('user') in chatroom.users.all():
            return Response(error_code.USER_IS_MEMBER, status=400)

        ChatroomInvitation.objects.get(receiver=receiver, chatroom=chatroom).delete()

        return Response(status=204)


class AcceptRequest(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chatroom_pk):
        chatroom = get_object_or_404(ChatRoom, pk=chatroom_pk)

        if not ChatroomInvitation.objects.filter(chatroom=chatroom, receiver=request.user).exists():
            return Response(error_code.INVITATION_DOESNT_EXISTS)

        invitation = ChatroomInvitation.objects.get(chatroom=chatroom, receiver=request.user)

        invitation.accept()

        return Response(status=201)


class RejectRequest(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, chatroom_pk):
        chatroom = get_object_or_404(ChatRoom, pk=chatroom_pk)

        if not ChatroomInvitation.objects.filter(chatroom=chatroom, receiver=request.user).exists():
            return Response(error_code.INVITATION_DOESNT_EXISTS)

        invitation = ChatroomInvitation.objects.get(chatroom=chatroom,
                                                    receiver=request.user)

        invitation.decline()

        return Response(status=204)


class SearchForChatroomUser(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, chatroom_pk):
        if request.query_params.get('name') is None or not request.query_params.get('name'):
            return Response(error_code.NO_NAME, status=400)

        name = request.query_params.get('name')

        chatroom = get_object_or_404(ChatRoom, pk=chatroom_pk)

        offset, limit = validate_offset_and_limit(request)

        queryset = get_user_model().objects.annotate(
            fullname=Concat('first_name', Value(' '), 'last_name'))

        users = queryset.filter(fullname__contains=name)[offset:limit]

        serializer = ChatroomUserSerializer(users, many=True, context={'request': request, 'chatroom': chatroom})
        return Response(serializer.data)
