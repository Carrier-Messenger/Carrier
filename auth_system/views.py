from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import AuthCode, EmailRenewCode


class ConfirmEmail(APIView):
    def get(self, request):
        code = request.GET.get('code')

        code = get_object_or_404(AuthCode, code=code)

        code.activate()

        return Response(status=200)


class ConfirmEmailChange(APIView):
    def get(self, request):
        code = request.GET.get('code')

        code = get_object_or_404(EmailRenewCode, code=code)

        code.activate()

        return Response(status=200)
