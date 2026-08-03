"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

from auction.consumers import AuctionConsumer
from social.consumers import ConversationConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(URLRouter([
        path('ws/auctions/<int:auction_id>/', AuctionConsumer.as_asgi()),
        path('ws/conversations/<int:conversation_id>/', ConversationConsumer.as_asgi()),
    ])),
})
