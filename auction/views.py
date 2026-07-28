from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Auction, Bid
from .serializers import AuctionSerializer, BidSerializer, BidPublicSerializer, PlaceBidSerializer
from .services import place_bid

class AuctionViewSet(viewsets.ModelViewSet):
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer

    def get_permissions(self):
        # Qualquer usuário autenticado pode LER leilões (participar do leilão
        # exige ver a lista/detalhe). Criar, editar ou apagar um leilão é
        # decisão de administração da plataforma (Cláusula 2.1.2 do contrato:
        # "Painel administrativo para criação de campanhas..."), então fica
        # restrito a is_staff — mesmo padrão já usado em ProductViewSet.
        if self.action in ['list', 'retrieve']:
            classes = [AllowAny]
        else:
            classes = [IsAdminUser]
        return [perm() for perm in classes]

class AuctionBidsView(generics.ListCreateAPIView):
    """
    GET  /api/v1/auctions/<auction_id>/bids/  -> histórico público de lances
         deste leilão (de todos os participantes, não só do usuário logado).
    POST /api/v1/auctions/<auction_id>/bids/  -> registra um novo lance neste
         leilão (o auction vem da URL, não do corpo da requisição).
    """
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        return PlaceBidSerializer if self.request.method == 'POST' else BidPublicSerializer

    def get_queryset(self):
        return (
            Bid.objects
            .filter(auction_id=self.kwargs['auction_id'])
            .select_related('user')
            .order_by('-price', 'bid_time')
        )

    def perform_create(self, serializer):
        auction = get_object_or_404(Auction, pk=self.kwargs['auction_id'])
        price = serializer.validated_data['price']

        try:
            bid = place_bid(
                user=self.request.user,
                auction=auction,
                price=price
            )
        except DjangoValidationError as e:
            raise DRFValidationError(str(e))

        serializer.instance = bid