from django.urls import path

from . import views

urlpatterns = [
    path('campaigns/', views.CampaignListView.as_view(), name='campaign-list'),
    path('campaigns/<int:campaign_pk>/admins/', views.CampaignAdminView.as_view(), name='campaign-admins'),
    path('campaigns/<int:campaign_pk>/join/', views.CampaignJoinView.as_view(), name='campaign-join'),
    path('campaigns/market-windows/', views.MarketWindowListView.as_view(), name='market-window-list'),
    path('campaigns/listings/', views.MarketListingListView.as_view(), name='market-listing-list'),
    path('campaigns/transfers/', views.TransferListView.as_view(), name='transfer-list'),
    path('campaigns/<int:campaign_pk>/list-player-for-sale/', views.ListPlayerForSaleView.as_view(), name='campaign-list-player-for-sale'),
    path('campaigns/<int:campaign_pk>/buy-direct/', views.BuyDirectView.as_view(), name='campaign-buy-direct'),
    path('campaigns/<int:campaign_pk>/propose-transfer/', views.ProposeTransferView.as_view(), name='campaign-propose-transfer'),
    path('campaigns/transfers/<int:pk>/respond/', views.RespondTransferView.as_view(), name='campaign-respond-transfer'),
    path('campaigns/<int:campaign_pk>/market-windows/create/', views.MarketWindowCreateView.as_view(), name='campaign-create-market-window'),
    path('campaigns/market-windows/<int:pk>/<str:action>/', views.MarketWindowOpenCloseView.as_view(), name='campaign-market-window-action'),
]
