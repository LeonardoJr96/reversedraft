from rest_framework import serializers
from .models import Auction, Bid
from .services import get_current_price

class AuctionSerializer(serializers.ModelSerializer):
    current_price = serializers.SerializerMethodField()

    class Meta:
        model = Auction
        fields = '__all__'
        read_only_fields = ['status', 'winner', 'number_of_bids', 'payment_deadline', 'starting_price']

    def get_current_price(self, obj):
        return get_current_price(obj)


class BidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bid
        fields = ['id', 'auction', 'price', 'bid_time']
        read_only_fields = ['bid_time']


class BidPublicSerializer(serializers.ModelSerializer):
    """Histórico de lances de um leilão, visível para todos os participantes
    autenticados (não só o dono do lance)."""
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Bid
        fields = ['id', 'auction', 'username', 'price', 'bid_time']


class PlaceBidSerializer(serializers.Serializer):
    """Usado só para registrar um novo lance: o leilão já vem da URL
    (/auctions/<auction_id>/bids/), então o único campo aceito é o preço."""
    price = serializers.DecimalField(max_digits=12, decimal_places=2)