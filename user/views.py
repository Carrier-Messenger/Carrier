from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models.functions import Concat
from django.db.models import Value
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializer import UserSerializer, MeSerializer
from friend.serializer import FriendSerializer
from friend.models import FriendList
from .imgs import cut
from . import error_code
from Messenger.general_functions import validate_offset_and_limit


class GetUser(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.user
        serializer = MeSerializer(query, context={'request': request})
        return Response(serializer.data)


class GetUserByID(APIView):
    def get(self, request, pk=None):
        query = get_object_or_404(get_user_model(), pk=pk)
        serializer = UserSerializer(query, context={'request': request})
        return Response(serializer.data)


class CreateUser(APIView):
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        password = request.data.get('password')

        if username is None:
            return Response(error_code.NO_USERNAME, status=400)
        if email is None:
            return Response(error_code.NO_EMAIL, status=400)
        if password is None:
            return Response(error_code.NO_PASSWORD, status=400)
        if first_name is None or not first_name:
            return Response(error_code.NO_FIRST_NAME, status=400)
        if last_name is None or not last_name:
            return Response(error_code.NO_LAST_NAME, status=400)

        if get_user_model().objects.filter(email=email).exists():
            return Response(error_code.EMAIL_EXISTS, status=400)
        if get_user_model().objects.filter(username=username).exists():
            return Response(error_code.USERNAME_EXISTS, status=400)

        user = get_user_model().objects.create_user(first_name=first_name,
                                                    last_name=last_name,
                                                    email=email,
                                                    password=password,
                                                    username=username)
        FriendList.objects.create(owner=user)
        return Response(status=201)


class GetUserByName(APIView):
    def get(self, request):
        if request.query_params.get('name') is not None and request.query_params.get('name'):
            offset, limit = validate_offset_and_limit(request)
            name = request.query_params.get('name')

            queryset = get_user_model().objects.annotate(
                fullname=Concat('first_name', Value(' '), 'last_name'))

            users = queryset.filter(fullname__startswith=name)[offset:limit]

            serializer = FriendSerializer(users, many=True, context={'request': request})
            return Response(serializer.data)
        return Response(error_code.NO_NAME, status=400)


class Authenticate(APIView):
    def get(self, request):
        content = {'authenticated': request.user.is_authenticated}
        return Response(content)


class AddProfilePicture(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser,)

    def post(self, request):
        user = request.user
        if request.FILES.get('pfp') is not None:
            img = request.FILES.get('pfp')
            cut(img, user)
            return Response(status=201)
        return Response(error_code.NO_PFP, status=400)
