from django.contrib.auth.models import BaseUserManager
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from friend.models import FriendList


class UserManager(BaseUserManager):
    def create_user(self, username, first_name, last_name, email, password=None):
        # password = validate_password(password=password)
        email = self.normalize_email(email)

        username = get_user_model().normalize_username(username)

        user = self.model(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(password)

        user.save(using=self._db)
        FriendList.objects.create(owner=user)

        return user

    def create_staffuser(self, username, first_name, last_name, email, password=None):
        user = self.create_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        user.is_staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, username, first_name, last_name, email, password=None):
        user = self.create_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
