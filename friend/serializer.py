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
                  'pfp']


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
