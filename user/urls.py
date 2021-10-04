from django.urls import path
from .views import GetUser, GetUserByID, CreateUser, GetUserByName, Authenticate, AddProfilePicture
from friend.views import InviteFriend, AcceptFriend, RejectFriend, RemoveFriend, CancelRequest, InvitesToMe


urlpatterns = [
    path('current-user/', GetUser.as_view()),
    path('<int:pk>/', GetUserByID.as_view()),
    path('create/', CreateUser.as_view()),
    path('by-name/', GetUserByName.as_view()),
    path('authenticate/', Authenticate.as_view()),
    path('add-pfp/', AddProfilePicture.as_view()),
    path('<int:receiver>/invite/', InviteFriend.as_view()),
    path('<int:sender>/accept/', AcceptFriend.as_view()),
    path('<int:sender>/reject/', RejectFriend.as_view()),
    path('<int:friend>/remove/', RemoveFriend.as_view()),
    path('<int:receiver>/cancel/', CancelRequest.as_view()),
    path('invites-to-me/', InvitesToMe.as_view()),
]
