from django.db import models


class FriendList(models.Model):
    owner = models.OneToOneField('auth_system.CustomUser', on_delete=models.CASCADE, related_name='friend_list')
    friends = models.ManyToManyField('auth_system.CustomUser', blank=True, related_name='friends')

    def __str__(self):
        return 'Friend list of ' + self.owner.username

    def add_friend(self, user):
        if user not in self.friends.all():
            self.friends.add(user)

    def remove_friend(self, user):
        if user in self.friends.all():
            self.friends.remove(user)

    def unfriend(self, user):
        self.remove_friend(user)
        friend_list = FriendList.objects.get(owner=user)
        friend_list.remove_friend(self.owner)

    def is_friend(self, user):
        if user in self.friends.all():
            return True
        return False


class FriendRequest(models.Model):
    sender = models.ForeignKey(
        'auth_system.CustomUser', related_name='sender', on_delete=models.CASCADE)
    receiver = models.ForeignKey(
        'auth_system.CustomUser', related_name='receiver', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'From {self.sender.username} to {self.receiver.username}'

    @classmethod
    def invite(cls, sender, receiver):
        if receiver == sender:
            return {"created": False}

        user_friend_list, created = FriendList.objects.get_or_create(
            owner=sender)

        if user_friend_list.is_friend(receiver):
            return {"created": False}

        if cls.objects.filter(sender=receiver, receiver=sender).exists():
            return {"created": False}

        instance, created = cls.objects.get_or_create(
            sender=sender, receiver=receiver)

        return {"created": created}

    def decline(self):
        self.delete()

    def accept(self):
        sender_friend_list = FriendList.objects.get(owner=self.sender)
        receiver_friend_list = FriendList.objects.get(owner=self.receiver)
        sender_friend_list.add_friend(self.receiver)
        receiver_friend_list.add_friend(self.sender)
        self.decline()
