from rest_framework import serializers
from .models import Conversation, Friendship, Message


class FriendshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friendship
        fields = '__all__'
        read_only_fields = ['requester', 'status', 'created_at', 'responded_at']


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id', 'type', 'campaign', 'participants', 'created_at']
        read_only_fields = fields


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['conversation', 'sender', 'created_at']
