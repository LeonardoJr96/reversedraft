from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Campaign, MarketWindow, MarketListing, Transfer
from .serializers import CampaignSerializer, MarketWindowSerializer, MarketListingSerializer, TransferSerializer
from . import services as campaign_services
from user.models import User
from team.serializers import TeamSerializer
from django.shortcuts import get_object_or_404


class CampaignListView(generics.ListCreateAPIView):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        name = data.pop('name')
        allowed = {key: data[key] for key in ('starting_balance', 'min_roster_size', 'max_roster_size', 'matches_per_market_cycle', 'transfer_policy') if key in data}
        campaign = campaign_services.create_campaign(request.user, name, **allowed)
        headers = self.get_success_headers(serializer.data)
        output = CampaignSerializer(campaign, context=self.get_serializer_context()).data
        return Response(output, status=status.HTTP_201_CREATED, headers=headers)


class CampaignAdminView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, campaign_pk):
        campaign = get_object_or_404(Campaign, pk=campaign_pk)
        user_id = request.data.get('user_id')
        target = get_object_or_404(User, pk=user_id)
        campaign_services.add_campaign_admin(request.user, campaign, target)
        return Response({'detail': 'admin adicionado'}, status=status.HTTP_200_OK)

    def delete(self, request, campaign_pk):
        campaign = get_object_or_404(Campaign, pk=campaign_pk)
        user_id = request.query_params.get('user_id')
        target = get_object_or_404(User, pk=user_id)
        campaign_services.remove_campaign_admin(request.user, campaign, target)
        return Response({'detail': 'admin removido'}, status=status.HTTP_200_OK)


class CampaignSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, campaign_pk):
        campaign = get_object_or_404(Campaign, pk=campaign_pk)
        if "starting_balance" not in request.data:
            return Response({"detail": "starting_balance is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            campaign = campaign_services.configure_starting_balance(request.user, campaign, request.data["starting_balance"])
        except Exception as exc:
            from django.core.exceptions import ValidationError
            if isinstance(exc, ValidationError):
                code = status.HTTP_403_FORBIDDEN if "administrador" in str(exc) else status.HTTP_400_BAD_REQUEST
                return Response({"detail": str(exc)}, status=code)
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CampaignSerializer(campaign).data)

class CampaignJoinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, campaign_pk):
        campaign = get_object_or_404(Campaign, pk=campaign_pk)
        campaign_services.join_campaign(request.user, campaign)
        return Response({'detail': 'entrada registrada'}, status=status.HTTP_200_OK)


class MarketWindowListView(generics.ListCreateAPIView):
    queryset = MarketWindow.objects.all()
    serializer_class = MarketWindowSerializer

    def post(self, request, *args, **kwargs):
        campaign_id = request.data.get('campaign')
        name = request.data.get('name')
        starts_at = request.data.get('starts_at')
        ends_at = request.data.get('ends_at')
        mode = request.data.get('mode', 'auction')
        player_count = request.data.get('player_count')
        random_selection = request.data.get('random_selection', True)
        per_player_mode = request.data.get('per_player_mode')

        if not campaign_id or not name:
            return Response({'detail': 'campaign and name are required'}, status=status.HTTP_400_BAD_REQUEST)

        campaign = __import__('campaigns').models.Campaign.objects.get(pk=campaign_id)
        # require admin
        campaign_services._require_admin(request.user, campaign)

        window = campaign_services.create_market_window(campaign, name, starts_at=starts_at, ends_at=ends_at, mode=mode, player_count=player_count, random_selection=random_selection, per_player_mode=per_player_mode)
        return Response(MarketWindowSerializer(window).data, status=status.HTTP_201_CREATED)


class MarketListingListView(generics.ListCreateAPIView):
    queryset = MarketListing.objects.all()
    serializer_class = MarketListingSerializer

    def post(self, request, *args, **kwargs):
        # Expect payload to include `market_window` (id) and `player_id`
        mw_id = request.data.get('market_window')
        player_id = request.data.get('player') or request.data.get('player_id')
        listing_type = request.data.get('listing_type', 'auction')
        price = request.data.get('price')
        if not mw_id or not player_id:
            return Response({'detail': 'market_window and player are required'}, status=status.HTTP_400_BAD_REQUEST)

        mw = __import__('campaigns').models.MarketWindow.objects.get(pk=mw_id)
        player = __import__('fifa_data').models.Player.objects.get(pk=player_id)

        listing = campaign_services.list_player_for_sale(request.user, mw.campaign, player, listing_type=listing_type, price=price)
        return Response(MarketListingSerializer(listing).data, status=status.HTTP_201_CREATED)


class TransferListView(generics.ListCreateAPIView):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer

    def post(self, request, *args, **kwargs):
        campaign_id = request.data.get('campaign')
        receiver_id = request.data.get('receiver') or request.data.get('receiver_id')
        offered = request.data.get('offered_players', [])
        requested = request.data.get('requested_players', [])
        if not campaign_id or not receiver_id:
            return Response({'detail': 'campaign and receiver are required'}, status=status.HTTP_400_BAD_REQUEST)

        campaign = Campaign.objects.get(pk=campaign_id)
        receiver = __import__('user').models.User.objects.get(pk=receiver_id)
        transfer = campaign_services.propose_transfer(campaign, request.user, receiver, offered_players=offered, requested_players=requested)
        return Response(TransferSerializer(transfer).data, status=status.HTTP_201_CREATED)


class ListPlayerForSaleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, campaign_pk):
        player_id = request.data.get('player_id')
        listing_type = request.data.get('listing_type', 'auction')
        price = request.data.get('price')

        campaign = get_object_or_404(Campaign, pk=campaign_pk)
        player = get_object_or_404(__import__('fifa_data').models.Player, pk=player_id)

        listing = campaign_services.list_player_for_sale(request.user, campaign, player, listing_type=listing_type, price=price)
        return Response(MarketListingSerializer(listing).data, status=status.HTTP_201_CREATED)


class BuyDirectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, campaign_pk):
        player_id = request.data.get('player_id')
        price = request.data.get('price')
        campaign = get_object_or_404(Campaign, pk=campaign_pk)
        player = get_object_or_404(__import__('fifa_data').models.Player, pk=player_id)

        team = campaign_services.buy_direct(request.user, campaign, player, price)
        return Response(TeamSerializer(team).data)


class ProposeTransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, campaign_pk):
        receiver_id = request.data.get('receiver_id')
        offered = request.data.get('offered_players', [])
        requested = request.data.get('requested_players', [])

        campaign = get_object_or_404(Campaign, pk=campaign_pk)
        receiver = get_object_or_404(__import__('user').models.User, pk=receiver_id)

        transfer = campaign_services.propose_transfer(campaign, request.user, receiver, offered_players=offered, requested_players=requested)
        return Response(TransferSerializer(transfer).data, status=status.HTTP_201_CREATED)


class RespondTransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        accepted = request.data.get('accepted', False)
        transfer = get_object_or_404(Transfer, pk=pk)
        transfer = campaign_services.respond_transfer(transfer, accepted, request.user)
        return Response(TransferSerializer(transfer).data)


class MarketWindowCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, campaign_pk):
        name = request.data.get('name')
        starts_at = request.data.get('starts_at')
        ends_at = request.data.get('ends_at')
        mode = request.data.get('mode', 'auction')
        player_count = request.data.get('player_count')
        random_selection = request.data.get('random_selection', True)
        per_player_mode = request.data.get('per_player_mode')

        campaign = get_object_or_404(Campaign, pk=campaign_pk)
        # require admin
        campaign_services._require_admin(request.user, campaign)

        window = campaign_services.create_market_window(campaign, name, starts_at=starts_at, ends_at=ends_at, mode=mode, player_count=player_count, random_selection=random_selection, per_player_mode=per_player_mode)
        return Response(MarketWindowSerializer(window).data, status=status.HTTP_201_CREATED)


class MarketWindowOpenCloseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, action):
        window = get_object_or_404(MarketWindow, pk=pk)
        campaign_services._require_admin(request.user, window.campaign)

        if action == 'open':
            window = campaign_services.open_market_window(window)
        elif action == 'close':
            window = campaign_services.close_market_window(window)
        else:
            return Response({'detail': 'invalid action'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(MarketWindowSerializer(window).data)


class MarketListingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        listing = get_object_or_404(MarketListing, pk=pk)
        try:
            campaign_services._require_admin(request.user, listing.market_window.campaign)
            listing = campaign_services.update_listing_type(request.user, listing, request.data.get('listing_type'))
        except Exception as exc:
            from django.core.exceptions import ValidationError
            if isinstance(exc, ValidationError):
                code = status.HTTP_403_FORBIDDEN if 'administrador' in str(exc) else status.HTTP_400_BAD_REQUEST
                return Response({'detail': str(exc)}, status=code)
            raise
        return Response(MarketListingSerializer(listing).data)
