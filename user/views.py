from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models.functions import Concat
from django.db.models import Value
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializer import UserSerializer, MeSerializer
from friend.serializer import FriendSerializer
from .imgs import cut
from . import error_code
from Carrier.general_functions import validate_offset_and_limit


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

        try:
            validate_password(password)
        except ValidationError as e:
            if 'This password is too commons.' in e:
                return Response(error_code.PASSWORD_TOO_COMMON, status=400)
            if 'This password is too short. It must contain at least 8 characters.' in e:
                return Response(error_code.PASSWORD_TOO_SHORT)
            if 'This password is entirely numeric.' in e:
                return Response(error_code.PASSWORD_IS_NUMERIC, status=400)

        user = get_user_model().objects.create_user(first_name=first_name,
                                                    last_name=last_name,
                                                    email=email,
                                                    password=password,
                                                    username=username)
        user.is_active = False
        user.save()
        user.create_code()
        user.send_confirmation_email()

        return Response(status=201)


class SendConfirmationEmail(APIView):
    def post(self, request):
        if request.data.get('email') is None:
            return Response(error_code.NO_EMAIL, status=400)

        email = request.data.get('email')

        if not get_user_model().objects.filter(email=email).exists():
            return Response(error_code.WRONG_EMAIL, status=400)

        user = get_user_model().objects.get(email=email)

        if user.is_active:
            return Response(error_code.USER_ALREADY_ACTIVE, status=400)

        user.code.renew()

        user.send_confirmation_email()

        return Response(status=204)


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


class EditUser(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user

        if request.data.get('first_name') is not None:
            user.first_name = request.data.get('first_name')

        if request.data.get('last_name') is not None:
            user.last_name = request.data.get('last_name')

        if request.data.get('email') is not None:
            email = request.data.get('email')

            try:
                validate_email(email)
            except ValidationError:
                return Response(error_code.INVALID_EMAIL, status=400)

            request.user.change_email(email)

        if request.data.get('new_password') is not None:
            password = request.data.get('new_password')

            old_password = request.data.get('password')

            if password is None:
                return Response(error_code.NO_PASSWORD, status=401)

            if not user.check_password(old_password):
                return Response(error_code.WRONG_PASSWORD, status=401)

            try:
                validate_password(old_password)
            except ValidationError as e:
                if 'This password is too commons.' in e:
                    return Response(error_code.PASSWORD_TOO_COMMON, status=400)
                if 'This password is too short. It must contain at least 8 characters.' in e:
                    return Response(error_code.PASSWORD_TOO_SHORT)
                if 'This password is entirely numeric.' in e:
                    return Response(error_code.PASSWORD_IS_NUMERIC, status=400)

            user.set_password(password)

        user.save()

        return Response(status=204)


class SendEmailChangeEmail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not hasattr(user, 'email_code'):
            return Response(error_code.NO_EMAIL_CODE, status=400)

        user.email_code.renew()

        user.send_email_change_email()

        return Response(status=200)


class Suicide(APIView):
    def delete(self, request):
        password = request.data.get('password')
        if password is None:
            return Response(error_code.NO_PASSWORD, status=401)

        user = request.user

        if not user.check_password(password):
            return Response(error_code.WRONG_PASSWORD, status=401)

        user.delete()
        return Response(status=204)


class Authenticate(APIView):
    def get(self, request):
        authenticated = request.user.is_authenticated
        content = {'authenticated': request.user.is_authenticated}
        if authenticated:
            return Response(content, 200)
        return Response(content, 401)


class AddProfilePicture(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser,)

    def post(self, request):
        user = request.user
        if request.FILES.get('pfp') is not None:
            img = request.FILES.get('pfp')

            if img.name.split('.')[-1] not in ['jpg', 'jpeg', 'png']:
                return Response(error_code.INVALID_EXTENSION, status=400)

            cut(img, user)
            return Response(status=201)
        return Response(error_code.NO_PFP, status=400)
