from django.shortcuts import render
from dj_rql.drf import RQLFilterBackend
from rest_framework import viewsets

from .models import Auction, Bid
from .serializers import AuctionSerializer, BidSerializer

class AuctionViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer

class BidViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    queryset = Bid.objects.all()
    serializer_class = BidSerializer