from django.contrib.auth import get_user_model
from django.db.models import Value, Q
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from itertools import chain
from Carrier.general_functions import validate_offset_and_limit
from . import error_code
from .models import ChatRoom, Message, ChatroomInvitation
from .serializer import GroupSerializer, MessageSerializer, ChatRoomInvitationSerializer, ChatroomUserSerializer


class GetUserChatRooms(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        not_none_chats = filter(
            lambda chat: True if chat.last_message is not None else False, ChatRoom.get_group_by_user(user=user)
        )
        none_chats = filter(
            lambda chat: False if chat.last_message is not None else True, ChatRoom.get_group_by_user(user=user)
        )
        groups = reversed(sorted(not_none_chats,  key=lambda chat: chat.last_message.created_at))
        all_groups = list(chain(groups, none_chats))
        serializer = GroupSerializer(all_groups, many=True, context={'request': request})
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

            last_message = get_object_or_404(Message, pk=last_message)
            qs = group.messages.filter(created_at__lte=last_message.created_at).order_by('-created_at')[offset:limit]
        else:
            qs = group.messages.all().order_by('-created_at')[offset:limit]

        serializer = MessageSerializer(qs,
                                       many=True,
                                       read_only=True,
                                       context={'request': request})

        return Response(serializer.data)


class GetChatRoomInfo(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, chatroom_pk):
        chat_room = get_object_or_404(ChatRoom, pk=chatroom_pk)

        if request.user not in chat_room.users.all():
            return Response(error_code.USER_NOT_MEMBER, status=403)

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

        serializer = GroupSerializer(chat_room, context={'request': request})

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

        receiver = get_object_or_404(get_user_model(), pk=request.data.get('user'))

        if receiver == request.user:
            return Response(error_code.CANT_INVITE_YOURSELF, status=400)

        if ChatroomInvitation.objects.filter(receiver=receiver, chatroom=chatroom).exists():
            return Response(error_code.SAME_INVITATION_EXISTS, status=400)

        if request.data.get('user') in chatroom.users.all():
            return Response(error_code.USER_IS_MEMBER, status=400)

        ChatroomInvitation.objects.create(sender=request.user, receiver=receiver, chatroom=chatroom)

        return Response(status=201)


class RemoveUser(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, chatroom_pk):
        chatroom = get_object_or_404(ChatRoom, pk=chatroom_pk)

        if request.user not in chatroom.creators.all():
            return Response(error_code.USER_NOT_ADMIN, status=403)

        if request.data.get('user') is None:
            return Response(error_code.USER_IS_NONE)

        user = get_object_or_404(get_user_model(), pk=request.data.get('user'))

        if user == request.user:
            return Response(error_code.CANT_REMOVE_YOURSELF, status=400)

        if request.data.get('user') in chatroom.users.all():
            return Response(error_code.USER_NOT_MEMBER, status=400)

        chatroom.users.remove(user)

        if user in chatroom.creators.all():
            chatroom.creators.remove(user)

        chatroom.save()

        return Response(status=201)


class CancelRequest(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, chatroom_pk):
        chatroom = get_object_or_404(ChatRoom, pk=chatroom_pk)

        if request.user not in chatroom.creators.all():
            return Response(error_code.USER_NOT_ADMIN, status=403)

        if request.data.get('user') is None:
            return Response(error_code.USER_IS_NONE, status=400)

        if not get_user_model().objects.filter(pk=request.data.get('user')).exists():
            return Response(error_code.NO_USER_WITH_PK, status=400)

        receiver = get_object_or_404(get_user_model(), pk=request.data.get('user'))

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

        invitation = get_object_or_404(ChatroomInvitation, chatroom=chatroom, receiver=request.user)

        invitation.accept()

        return Response(status=201)


class RejectRequest(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, chatroom_pk):
        chatroom = get_object_or_404(ChatRoom, pk=chatroom_pk)

        if not ChatroomInvitation.objects.filter(chatroom=chatroom, receiver=request.user).exists():
            return Response(error_code.INVITATION_DOESNT_EXISTS)

        invitation = get_object_or_404(ChatroomInvitation, chatroom=chatroom, receiver=request.user)

        invitation.decline()

        return Response(status=204)


class LeaveChatroom(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, chatroom_pk):
        chatroom = get_object_or_404(ChatRoom, pk=chatroom_pk)
        user = request.user

        if user not in chatroom.users.all():
            return Response(error_code.USER_NOT_MEMBER, status=400)

        chatroom.users.remove(user)

        if user in chatroom.creators.all():
            chatroom.creators.remove(user)

        chatroom.save()

        if len(chatroom.users.all()) <= 0:
            chatroom.delete()

        return Response(status=204)


class DeleteChatRoom(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, chatroom_pk):
        chatroom = get_object_or_404(ChatRoom, pk=chatroom_pk)

        if request.user not in chatroom.creators.all():
            return Response(error_code.USER_NOT_ADMIN, status=400)

        chatroom.delete()

        return Response(status=204)


class AddAdmin(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chatroom_pk):
        chatroom = get_object_or_404(ChatRoom, pk=chatroom_pk)

        if request.user not in chatroom.creators.all():
            return Response(error_code.USER_NOT_ADMIN, status=403)

        user = request.data.get('user')

        user = get_object_or_404(get_user_model(), pk=user)

        if user not in chatroom.users.all():
            return Response(error_code.PK_USER_NOT_MEMBER, status=400)

        chatroom.creators.add(user)
        chatroom.save()

        return Response(status=200)


class DeleteAdmin(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, chatroom_pk):
        chatroom = get_object_or_404(ChatRoom, pk=chatroom_pk)

        if request.user not in chatroom.creators.all():
            return Response(error_code.USER_NOT_ADMIN, status=403)

        user = request.data.get('user')

        user = get_object_or_404(get_user_model(), pk=user)

        if user not in chatroom.creators.all():
            return Response(error_code.PK_USER_NOT_ADMIN, status=400)

        chatroom.creators.remove(user)
        chatroom.save()

        return Response(status=200)


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

        users = queryset.filter(Q(fullname__startswith=name) | Q(username__contains=name))[offset:limit]

        serializer = ChatroomUserSerializer(users, many=True, context={'request': request, 'chatroom': chatroom})
        return Response(serializer.data)
