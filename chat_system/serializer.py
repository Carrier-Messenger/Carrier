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
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'author', 'content', 'created_at', 'is_mine']

    def get_is_mine(self, message):
        request = self.context.get('request')
        return request is not None and request.user == message.author


class WSMessageSerializer(serializers.ModelSerializer):
    author = FriendSerializer()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'author', 'content', 'created_at', 'is_mine']

    def get_is_mine(self, message):
        user = self.context.get('user')
        return user is not None and user == message.author


class GroupSerializer(serializers.ModelSerializer):
    users = FriendSerializer(many=True, read_only=True)
    creators = FriendSerializer(many=True, read_only=True)
    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = '__all__'

    def get_is_admin(self, group):
        request = self.context.get('request')
        return request is not None and request.user in group.creators.all()


class SilentGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'image']


class ChatRoomInvitationSerializer(serializers.ModelSerializer):
    chatroom = SilentGroupSerializer()
    sender = FriendSerializer()

    class Meta:
        model = ChatroomInvitation
        fields = ['chatroom', 'sender']
