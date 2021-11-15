import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import Message, ChatRoom, MessageImage
from .serializer import WSMessageSerializer
from .base64 import decode_base64_to_image


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        if not ChatRoom.objects.get(pk=self.room_name).is_user_in_chat_room(self.scope['user']):
            self.close()

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message')
        images = text_data_json.get('images')

        if not message and not images:
            return

        user = self.scope['user']
        chat_room = ChatRoom.objects.get(pk=self.room_name)

        message = Message.objects.create(author=user, chat_room=chat_room, content=message)
        message_pk = message.pk

        if images is not None and isinstance(images, list):
            for image in images:
                MessageImage.objects.create(author=user, message=message, image=decode_base64_to_image(image))

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_pk
            }
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']
        serializer = WSMessageSerializer(Message.objects.get(pk=message), context={'user': self.scope['user']})
        # Send message to WebSocket
        self.send(text_data=json.dumps(serializer.data))
