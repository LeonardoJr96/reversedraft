from rest_framework import serializers
from products.models import Product
from products.serializers import ProductSerializer
from .models import Auction, Bid, PricingMode
from .services import get_current_price

class AuctionSerializer(serializers.ModelSerializer):
    current_price = serializers.SerializerMethodField()
    product = ProductSerializer(read_only=True)
    starting_price = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=False)
    min_increment = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=False)

    class Meta:
        model = Auction
        fields = '__all__'
        read_only_fields = ['status', 'winner', 'number_of_bids', 'payment_deadline']

    def get_current_price(self, obj):
        return get_current_price(obj)


class CreateAuctionSerializer(serializers.Serializer):
    """
    Usado só na criação (POST /auctions/): não é ModelSerializer porque
    os campos de entrada não batem 1:1 com o model — quem calcula
    starting_price/time_starting/time_ending é o service create_auction(),
    não o cliente.
    """
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    pricing_mode = serializers.ChoiceField(choices=Auction._meta.get_field('pricing_mode').choices)
    duration_minutes = serializers.IntegerField(min_value=1)
    manual_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    min_increment = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=1)

    def validate(self, data):
        if data['pricing_mode'] == PricingMode.MANUAL and 'manual_price' not in data:
            raise serializers.ValidationError(
                {"manual_price": "Obrigatório quando pricing_mode = 'manual'."}
            )
        return data


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