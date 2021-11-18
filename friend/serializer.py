from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import FriendList, FriendRequest


class FriendSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = get_user_model()
        fields = ['id',
                  'username',
                  'first_name',
                  'last_name',
                  'full_name',
                  'pfp',
                  'friends']

    def get_friends(self, user):
        query_set = FriendList.objects.get(owner=user)
        return FriendListSerializer(query_set, context={'request': self.context.get('request')}).data.get('friends')


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
