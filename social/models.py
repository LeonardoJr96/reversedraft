from django.conf import settings
from django.db import models


class Friendship(models.Model):
    STATUS_CHOICES = [('pending', 'Pendente'), ('accepted', 'Aceito'), ('declined', 'Recusado')]
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_friend_requests')
    addressee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_friend_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['requester', 'addressee'], name='unique_friendship_direction')]


class Conversation(models.Model):
    TYPE_CHOICES = [('direct', 'Direto'), ('campaign', 'Campanha')]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    campaign = models.OneToOneField('campaigns.Campaign', null=True, blank=True, on_delete=models.CASCADE, related_name='chat')
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
