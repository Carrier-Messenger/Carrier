from django.urls import path
from .views import *


urlpatterns = [
    path('create/', CreateRoom.as_view()),
    path('get-user-groups/', GetUserChatRoom.as_view()),
    path('get-messages/<int:room_pk>/', GetChatRoomMessages.as_view()),
    path('invitations-to-me/', InvitesToMe.as_view()),
    path('<int:chat_room_pk>/', GetChatRoomInfo.as_view()),
    path('<int:chatroom_pk>/invite/', InviteUser.as_view()),
    path('<int:chatroom_pk>/accept/', AcceptRequest.as_view()),
    path('<int:chatroom_pk>/reject/', RejectRequest.as_view()),
    path('<int:chatroom_pk>/cancel/', CancelRequest.as_view()),
    path('<int:chatroom_pk>/search-user/', SearchForChatroomUser.as_view()),
]
