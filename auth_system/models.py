from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from .user_manager import UserManager
from Messenger.settings import DEFAULT_FROM_EMAIL
from django.core.mail import send_mail
import random
import string


class CustomUser(AbstractUser):
    pfp = models.ImageField(upload_to="users/", default="users/default.png")

    REQUIRED_FIELDS = ['password', 'first_name', 'last_name', 'email']

    objects = UserManager()

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def send_confirmation_email(self):
        send_mail("Your registration is almost completed",
                  f"To complete registration paste this code on our website\n\n{self.code.code}\n\nSorki że bez przekierowania ale google usuwa mi linki >:(",
                  DEFAULT_FROM_EMAIL,
                  [self.email])

    def create_code(self):
        self.code = AuthCode.objects.create(user=self, code=AuthCode.create_auth_code())


class AuthCode(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='code', null=True)
    code = models.CharField(max_length=255, unique=True)

    @staticmethod
    def create_code():
        characters = string.ascii_letters + string.digits
        code = ''.join(random.choice(characters) for i in range(255))
        return code

    @classmethod
    def create_auth_code(cls):
        while True:
            code = cls.create_code()
            if not AuthCode.objects.filter(code=code).exists():
                break

        return code

    def activate(self):
        self.user.is_active = True
        self.user.save()

        self.delete()

