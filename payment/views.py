# payment/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from auction.models import Auction
from .services import pay_for_auction, recharge_balance
from .serializers import TransactionSerializer
from .models import Transaction


class PayAuctionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, auction_id):
        auction = Auction.objects.filter(pk=auction_id).first()
        if auction is None:
            return Response({"detail": "Leilão não encontrado."}, status=404)
        try:
            txn = pay_for_auction(request.user, auction)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)
        return Response(TransactionSerializer(txn).data, status=201)


class MyTransactionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Transaction.objects.filter(user=request.user).select_related('auction')
        return Response(TransactionSerializer(qs, many=True).data)