from rest_framework import serializers

from .models import Campaign, MarketWindow, MarketListing, Transfer


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = '__all__'


class MarketWindowSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketWindow
        fields = '__all__'


class MarketListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketListing
        fields = '__all__'


class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = '__all__'
