from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from campaigns.models import Campaign, CampaignMembership
from user.models import User
from .models import Friendship, Conversation
from .serializers import ConversationSerializer, FriendshipSerializer, MessageSerializer
from . import services


def _error(exc, forbidden=False):
    return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN if forbidden else status.HTTP_400_BAD_REQUEST)


class FriendRequestView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            friendship = services.send_friend_request(request.user, get_object_or_404(User, pk=request.data.get('addressee_id')))
            return Response(FriendshipSerializer(friendship).data, status=status.HTTP_201_CREATED)
        except ValidationError as exc:
            return _error(exc)


class FriendRequestRespondView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        friendship = get_object_or_404(Friendship, pk=pk)
        try:
            friendship = services.respond_friend_request(friendship, bool(request.data.get('accepted')), request.user)
            return Response(FriendshipSerializer(friendship).data)
        except ValidationError as exc:
            return _error(exc, forbidden=friendship.addressee_id != request.user.id)


class FriendsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response([{'id': user.id, 'username': user.username} for user in services.list_friends(request.user)])


class DirectConversationView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, user_id):
        try:
            conversation = services.get_or_create_direct_conversation(request.user, get_object_or_404(User, pk=user_id))
            return Response(ConversationSerializer(conversation).data)
        except ValidationError as exc:
            return _error(exc)


class CampaignConversationView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, pk=campaign_id)
        if not CampaignMembership.objects.filter(campaign=campaign, user=request.user).exists() and not campaign.admins.filter(user=request.user).exists():
            return Response({'detail': 'Você não participa desta campanha.'}, status=status.HTTP_403_FORBIDDEN)
        return Response(ConversationSerializer(services.get_or_create_campaign_conversation(campaign)).data)


class ConversationMessagesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        try:
            limit = int(request.query_params.get('limit', 50))
            messages = list(services.list_messages(request.user, conversation, limit, request.query_params.get('before_id')))
            return Response({'messages': MessageSerializer(messages, many=True).data, 'has_more': len(messages) >= min(max(limit, 1), 100)})
        except (ValidationError, ValueError) as exc:
            return _error(exc, forbidden=isinstance(exc, ValidationError))
    def post(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        try:
            message = services.send_message(request.user, conversation, request.data.get('text'))
            return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
        except ValidationError as exc:
            return _error(exc, forbidden='não participa' in str(exc))
