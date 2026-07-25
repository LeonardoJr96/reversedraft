from rest_framework.routers import DefaultRouter
from .views import BidViewSet, AuctionViewSet

router = DefaultRouter()
router.register('bids', BidViewSet, basename='bid')
router.register('auctions', AuctionViewSet, basename='auction')

urlpatterns = router.urls