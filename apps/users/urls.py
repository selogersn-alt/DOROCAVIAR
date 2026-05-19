from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    register_view, dashboard_view, ProfileUpdateView, public_profile_view,
    ChatListView, ChatDetailView, AcceptFriendRequestView, SendFriendRequestView,
    chat_poll_view, notification_count_view, FollowUserView, notification_list_view,
    FriendsListView
)
from .views_sse import sse_notifications_stream

urlpatterns = [
    path('signup/', register_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/<str:username>/', public_profile_view, name='public_profile'),
    path('profile/<str:username>/follow/', FollowUserView.as_view(), name='follow_user'),
    path('friends/', FriendsListView.as_view(), name='friends_list'),
    
    # Messagerie & Notifications
    path('sse/', sse_notifications_stream, name='sse_stream'),
    path('messages/', ChatListView.as_view(), name='chat_list'),
    path('notifications/', notification_list_view, name='notifications'),
    path('notifications/count/', notification_count_view, name='notification_count'),
    path('messages/<str:username>/', ChatDetailView.as_view(), name='chat_detail'),
    path('messages/<str:username>/poll/', chat_poll_view, name='chat_poll'),
    path('friends/accept/<int:request_id>/', AcceptFriendRequestView.as_view(), name='accept_friend'),
    path('friends/send/<str:username>/', SendFriendRequestView.as_view(), name='send_friend'),
]
