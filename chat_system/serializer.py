from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import ChatRoom, Message, ChatroomInvitation, MessageImage
from friend.serializer import FriendSerializer


class ChatroomUserSerializer(FriendSerializer):
    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['id',
                  'username',
                  'first_name',
                  'last_name',
                  'full_name',
                  'pfp',
                  'friends',
                  'is_admin']

    def get_is_admin(self, user):
        chatroom = self.context.get('chatroom')
        return user in chatroom.creators.all()


class ChatroomUserSearchSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    is_invited = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    is_me = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['id',
                  'username',
                  'first_name',
                  'last_name',
                  'full_name',
                  'pfp',
                  'is_invited',
                  'is_member',
                  'is_admin',
                  'is_me']

    def get_is_invited(self, user):
        chatroom = self.context.get('chatroom')
        return ChatroomInvitation.objects.filter(chatroom=chatroom, receiver=user).exists()

    def get_is_member(self, user):
        chatroom = self.context.get('chatroom')
        return user in chatroom.users.all()

    def get_is_admin(self, user):
        chatroom = self.context.get('chatroom')
        return user in chatroom.creators.all()

    def get_is_me(self, user):
        request = self.context.get('request')
        return request.user == user


class MessageImageSerializer(serializers.ModelSerializer):
    url = serializers.ImageField(use_url=True, source='image')

    class Meta:
        model = MessageImage
        fields = ['url']


class MessageSerializer(serializers.ModelSerializer):
    author = FriendSerializer()
    is_mine = serializers.SerializerMethodField()
    images = MessageImageSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'author', 'content', 'created_at', 'is_mine', 'images']

    def get_is_mine(self, message):
        request = self.context.get('request')
        return request is not None and request.user == message.author


class WSMessageSerializer(serializers.ModelSerializer):
    author = FriendSerializer()
    is_mine = serializers.SerializerMethodField()
    images = MessageImageSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'author', 'content', 'created_at', 'is_mine', 'images']

    def get_is_mine(self, message):
        user = self.context.get('user')
        return user is not None and user == message.author


class GroupSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()
    creators = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    last_message = MessageSerializer(allow_null=True)

    class Meta:
        model = ChatRoom
        fields = '__all__'

    def get_is_admin(self, group):
        request = self.context.get('request')
        return request is not None and request.user in group.creators.all()

    def get_users(self, group):
        context = {'chatroom': group}
        context.update(self.context)
        return ChatroomUserSerializer(group.users.all(), many=True, read_only=True, context=context).data

    def get_creators(self, group):
        context = {'chatroom': group}
        context.update(self.context)
        return ChatroomUserSerializer(group.creators.all(), many=True, read_only=True, context=context).data


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
