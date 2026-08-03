from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Conversation


class ConversationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        if not user.is_authenticated or not await self._is_participant(user.id):
            await self.close(code=4403)
            return
        self.group_name = f'conversation_{self.conversation_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def message_created(self, event):
        await self.send_json(event['payload'])

    @database_sync_to_async
    def _is_participant(self, user_id):
        return Conversation.objects.filter(pk=self.conversation_id, participants__id=user_id).exists()
