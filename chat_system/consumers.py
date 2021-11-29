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
        action = text_data_json.get('action')

        if action == 'send':
            message = text_data_json.get('message')
            images = text_data_json.get('images')

            if not message and not images:
                return

            user = self.scope['user']
            chat_room = ChatRoom.objects.get(pk=self.room_name)

            if user not in chat_room.users.all():
                self.disconnect()
                return

            if len(message) > Message._meta.get_field('content').max_length:
                return

            message = Message.objects.create(author=user, chat_room=chat_room, content=message)
            message_pk = message.pk

            if images is not None and isinstance(images, list):
                if len(images) > Message.max_images:
                    return

                for image in images:
                    decoded_image = decode_base64_to_image(image)
                    if decoded_image.name.split('.')[-1] not in ['jpg', 'jpeg', 'png']:
                        return

                    MessageImage.objects.create(author=user, message=message, image=decoded_image)

            # Send message to room group
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'send_message',
                    'message': message_pk
                }
            )
        elif action == 'edit':
            message_pk = text_data_json.get('message_pk')
            images = text_data_json.get('images')

            if not message_pk:
                return

            message = Message.objects.get(pk=message_pk)

            if message.author != self.scope['user']:
                return

            message.content = text_data_json.get('content')
            message.save()

            if images is not None and isinstance(images, list):
                if len(images) > Message.max_images:
                    return

                message.images.all().delete()

                for image in images:
                    decoded_image = decode_base64_to_image(image)
                    if decoded_image.name.split('.')[-1] not in ['jpg', 'jpeg', 'png']:
                        return

                    MessageImage.objects.create(author=self.scope['user'],
                                                message=message,
                                                image=decoded_image)

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'edit_message',
                    'message': message_pk
                }
            )

        elif action == 'delete':
            message_pk = text_data_json.get('message_pk')

            if not message_pk:
                return

            if not Message.objects.filter(pk=message_pk).exists():
                return

            message = Message.objects.get(pk=message_pk)
            message.deleted = True
            message.save()

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'delete_message',
                    'message': message_pk
                }
            )

        else:
            self.disconnect()

    # Receive message from room group
    def send_message(self, event):
        message = event['message']
        serializer = WSMessageSerializer(Message.objects.get(pk=message), context={'user': self.scope['user'],
                                                                                   'action': 'send'})
        # Send message to WebSocket
        self.send(text_data=json.dumps(serializer.data))

    # Receive message from room group
    def edit_message(self, event):
        message = event['message']
        serializer = WSMessageSerializer(Message.objects.get(pk=message), context={'user': self.scope['user'],
                                                                                   'action': 'edit'})
        # Send message to WebSocket
        self.send(text_data=json.dumps(serializer.data))

    # Receive message from room group
    def delete_message(self, event):
        message = event['message']
        serializer = WSMessageSerializer(Message.objects.get(pk=message), context={'user': self.scope['user'],
                                                                                   'action': 'delete'})
        # Send message to WebSocket
        self.send(text_data=json.dumps(serializer.data))
