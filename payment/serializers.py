# payment/serializers.py
from rest_framework import serializers
from decimal import Decimal
from .models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'type', 'status', 'amount', 'balance_after', 'auction', 'notes', 'created_at']
class AdminRechargeSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))