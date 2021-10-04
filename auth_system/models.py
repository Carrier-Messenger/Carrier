from django.contrib.auth.models import AbstractUser
from django.db import models
from .user_manager import UserManager


class CustomUser(AbstractUser):
    pfp = models.ImageField(upload_to="users/", default="users/default.png")

    REQUIRED_FIELDS = ['password', 'first_name', 'last_name', 'email']

    objects = UserManager()

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
