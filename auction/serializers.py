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