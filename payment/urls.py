# payment/urls.py
from django.urls import path
from .views import PayAuctionView, MyTransactionsView, AdminRechargeBalanceView

urlpatterns = [
    path('auctions/<int:auction_id>/pay/', PayAuctionView.as_view()),
    path('me/', MyTransactionsView.as_view()),
    path('admin/recharge/', AdminRechargeBalanceView.as_view()),
]