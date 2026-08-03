from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Auction


class AuctionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        self.auction_id = self.scope['url_route']['kwargs']['auction_id']
        if not user.is_authenticated or not await self._auction_exists():
            await self.close(code=4403)
            return
        self.group_name = f'auction_{self.auction_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def bid_placed(self, event):
        await self.send_json(event['payload'])

    @database_sync_to_async
    def _auction_exists(self):
        return Auction.objects.filter(pk=self.auction_id).exists()
