from django.db import models
from django.contrib.auth import get_user_model


class ChatRoom(models.Model):
    creators = models.ManyToManyField(get_user_model(), related_name='my_groups')
    image = models.ImageField(upload_to="chatrooms/", default="chatrooms/default.png")
    users = models.ManyToManyField(get_user_model(), related_name='chatrooms')
    name = models.CharField(max_length=75, blank=False)

    @property
    def last_message(self):
        if len(self.messages.all()) == 0:
            return None

        return self.messages.all().order_by('-created_at').first()

    def connect_user(self, user):
        if user not in self.users.all():
            self.user.add(user)
            self.save()

    def disconnect(self, user):
        if user in self.users.all():
            self.users.remove(user)
            self.save()

    def is_user_in_chat_room(self, user):
        x = user in self.users.all()
        return x

    @staticmethod
    def get_group_by_user(user):
        groups = ChatRoom.objects.filter(users__in=[user])
        return groups

    @property
    def group_name(self):
        return f'PublicChatRoom-{self.id}'

    def __str__(self):
        return self.name


class Message(models.Model):
    author = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages', max_length=2000)
    content = models.TextField(max_length=2000, blank=False, null=False)
    created_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    edited = models.BooleanField(default=False)

    max_images = 100

    def __str__(self):
        return self.content


class MessageImage(models.Model):
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to="messages/")

    def __str__(self):
        return self.image.url


class ChatroomInvitation(models.Model):
    chatroom = models.ForeignKey(ChatRoom, related_name='invitations', on_delete=models.CASCADE)
    sender = models.ForeignKey(get_user_model(), related_name='chatroom_invitation_from_me', on_delete=models.CASCADE)
    receiver = models.ForeignKey(get_user_model(), related_name='chatroom_invitations', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'From chatroom {self.chatroom.name} (from {self.sender.username}) to {self.receiver.username}'

    def decline(self):
        self.delete()

    def accept(self):
        self.chatroom.users.add(self.receiver)
        self.delete()
