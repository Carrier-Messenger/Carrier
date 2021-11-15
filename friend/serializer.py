from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import FriendList, FriendRequest


class FriendSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    friend_type = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['id',
                  'username',
                  'first_name',
                  'last_name',
                  'full_name',
                  'pfp',
                  'friends',
                  'friend_type']

    def get_friends(self, user):
        query_set = FriendList.objects.get(owner=user)
        return FriendListSerializer(query_set, context={'request': self.context.get('request')}).data.get('friends')

    def get_friend_type(self, user):
        request_user = self.context.get('request').user
        if not request_user.is_authenticated:
            return "none"

        if FriendRequest.objects.filter(sender=user, receiver=request_user).exists():
            return "requested"
        elif FriendRequest.objects.filter(sender=request_user, receiver=user).exists():
            return "invited"
        elif request_user.friend_list.is_friend(user):
            return "friend"
        else:
            return "none"


class FriendListSerializer(serializers.ModelSerializer):
    friends = FriendSerializer(many=True, read_only=True)

    class Meta:
        model = FriendList
        fields = ['friends']


class FriendRequestSerializer(serializers.ModelSerializer):
    sender = FriendSerializer()
    receiver = FriendSerializer()

    class Meta:
        model = FriendRequest
        fields = '__all__'
