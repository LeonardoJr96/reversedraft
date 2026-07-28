from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import AuctionViewSet, AuctionBidsView

router = DefaultRouter()
router.register('auctions', AuctionViewSet, basename='auction')

urlpatterns = [
    # GET  -> lista pública de todos os lances deste leilão (todos os participantes)
    # POST -> registra um novo lance neste leilão
    path('auctions/<int:auction_id>/bids/', AuctionBidsView.as_view(), name='auction-bids'),
] + router.urls