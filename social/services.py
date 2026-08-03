from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Conversation, Friendship, Message


def send_friend_request(requester, addressee):
    if requester == addressee:
        raise ValidationError('Você não pode adicionar a si mesmo.')
    if Friendship.objects.filter(
        (models.Q(requester=requester) & models.Q(addressee=addressee)) |
        (models.Q(requester=addressee) & models.Q(addressee=requester))
    ).exists():
        raise ValidationError('Já existe uma solicitação ou amizade entre vocês.')
    return Friendship.objects.create(requester=requester, addressee=addressee)


def respond_friend_request(friendship, accepted, responder):
    if friendship.addressee_id != responder.id:
        raise ValidationError('Apenas o destinatário pode responder este pedido.')
    if friendship.status != 'pending':
        raise ValidationError('Este pedido já foi respondido.')
    friendship.status = 'accepted' if accepted else 'declined'
    friendship.responded_at = timezone.now()
    friendship.save(update_fields=['status', 'responded_at'])
    return friendship


def list_friends(user):
    accepted = Friendship.objects.filter(status='accepted').filter(models.Q(requester=user) | models.Q(addressee=user))
    ids = [friendship.addressee_id if friendship.requester_id == user.id else friendship.requester_id for friendship in accepted]
    return get_user_model().objects.filter(id__in=ids)


def are_friends(user_a, user_b):
    return Friendship.objects.filter(status='accepted').filter(
        (models.Q(requester=user_a) & models.Q(addressee=user_b)) |
        (models.Q(requester=user_b) & models.Q(addressee=user_a))
    ).exists()


def get_or_create_direct_conversation(user_a, user_b):
    if not are_friends(user_a, user_b):
        raise ValidationError('Vocês precisam ser amigos para conversar.')
    existing = Conversation.objects.filter(type='direct', participants=user_a).filter(participants=user_b).first()
    if existing:
        return existing
    with transaction.atomic():
        conversation = Conversation.objects.create(type='direct')
        conversation.participants.set([user_a, user_b])
    return conversation


def get_or_create_campaign_conversation(campaign):
    conversation, created = Conversation.objects.get_or_create(type='campaign', campaign=campaign)
    conversation.participants.add(*campaign.memberships.values_list('user_id', flat=True))
    return conversation


def _require_participant(user, conversation):
    if not conversation.participants.filter(pk=user.pk).exists():
        raise ValidationError('Você não participa desta conversa.')


def send_message(user, conversation, text):
    _require_participant(user, conversation)
    if not text or not text.strip():
        raise ValidationError('Mensagem vazia.')
    message = Message.objects.create(conversation=conversation, sender=user, text=text.strip())
    transaction.on_commit(lambda: _broadcast_message(message))
    return message


def _broadcast_message(message):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f'conversation_{message.conversation_id}',
        {'type': 'message.created', 'payload': {
            'type': 'message.created', 'id': message.id,
            'conversation_id': message.conversation_id, 'sender_id': message.sender_id,
            'text': message.text, 'created_at': message.created_at.isoformat(),
        }},
    )


def list_messages(user, conversation, limit=50, before_id=None):
    _require_participant(user, conversation)
    query = conversation.messages.order_by('-id')
    if before_id:
        query = query.filter(id__lt=before_id)
    return query[:max(1, min(int(limit), 100))]
