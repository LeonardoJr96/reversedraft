from django.urls import path
from . import views

urlpatterns = [
    path('social/friend-requests/', views.FriendRequestView.as_view()),
    path('social/friend-requests/<int:pk>/respond/', views.FriendRequestRespondView.as_view()),
    path('social/friends/', views.FriendsView.as_view()),
    path('social/conversations/direct/<int:user_id>/', views.DirectConversationView.as_view()),
    path('social/conversations/campaign/<int:campaign_id>/', views.CampaignConversationView.as_view()),
    path('social/conversations/<int:pk>/messages/', views.ConversationMessagesView.as_view()),
]
