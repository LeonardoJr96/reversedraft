# payment/urls.py
from django.urls import path
from .views import PayAuctionView, MyTransactionsView

urlpatterns = [
    path('auctions/<int:auction_id>/pay/', PayAuctionView.as_view()),
    path('me/', MyTransactionsView.as_view()),
]