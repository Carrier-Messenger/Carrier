from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import ChatRoom, Message, ChatroomInvitation
from friend.serializer import FriendSerializer


class ChatroomUserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    is_invited = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['id',
                  'username',
                  'first_name',
                  'last_name',
                  'full_name',
                  'pfp',
                  'is_invited',
                  'is_member']

    def get_is_invited(self, user):
        chatroom = self.context.get('chatroom')
        return ChatroomInvitation.objects.filter(chatroom=chatroom, receiver=user).exists()

    def get_is_member(self, user):
        chatroom = self.context.get('chatroom')
        return user in chatroom.users.all()


class MessageSerializer(serializers.ModelSerializer):
    author = FriendSerializer()

    class Meta:
        model = Message
        fields = '__all__'


class WSMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'


class GroupSerializer(serializers.ModelSerializer):
    users = FriendSerializer(many=True, read_only=True)
    creators = FriendSerializer(many=True, read_only=True)

    class Meta:
        model = ChatRoom
        fields = '__all__'


class ChatRoomInvitationSerializer(serializers.ModelSerializer):
    chatroom = GroupSerializer()
    receiver = FriendSerializer()

    class Meta:
        model = ChatroomInvitation
        fields = ['chatroom', 'receiver']
