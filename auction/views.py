from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Auction, Bid
from .serializers import AuctionSerializer, BidSerializer
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
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [perm() for perm in permission_classes]

class BidViewSet(viewsets.ModelViewSet):
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Bid.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        auction = serializer.validated_data['auction']
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