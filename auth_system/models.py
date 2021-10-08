from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from .user_manager import UserManager
from Carrier.settings import DEFAULT_FROM_EMAIL
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
                  f"To complete registration paste this code on our website\n\n{self.code.code}",
                  DEFAULT_FROM_EMAIL,
                  [self.email])

    def change_email(self, email):
        if hasattr(self, 'email_code'):
            self.email_code.renew()
            self.email_code.email = email
            self.email_code.save()
        else:
            EmailRenewCode.objects.create(user=self, email=email, code=EmailRenewCode.create_auth_code())

        self.send_email_change_email()

    def send_email_change_email(self):
        send_mail("Email change",
                  f"To change your email paste this code on our website\n\n{self.email_code.code}",
                  DEFAULT_FROM_EMAIL,
                  [self.email_code.email])

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

    def renew(self):
        self.code = self.create_auth_code()
        self.save()

    def activate(self):
        self.user.is_active = True
        self.user.save()

        self.delete()


class EmailRenewCode(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='email_code', null=True)
    email = models.EmailField()
    code = models.CharField(max_length=255, unique=True)

    @staticmethod
    def create_auth_code():
        while True:
            code = AuthCode.create_code()
            if not EmailRenewCode.objects.filter(code=code).exists():
                break

        return code

    def renew(self):
        self.code = self.create_auth_code()
        self.save()

    def activate(self):
        self.user.email = self.email
        self.user.save()

        self.delete()
