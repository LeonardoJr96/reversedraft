# payment/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.exceptions import ValidationError

from auction.models import Auction
from .services import pay_for_auction, recharge_balance
from .serializers import TransactionSerializer, AdminRechargeSerializer
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
class AdminRechargeBalanceView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = AdminRechargeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from user.models import User
        target = User.objects.filter(pk=serializer.validated_data["user_id"]).first()
        if target is None:
            return Response({"detail": "Usuário não encontrado."}, status=404)
        try:
            transaction = recharge_balance(target, serializer.validated_data["amount"])
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(TransactionSerializer(transaction).data, status=201)