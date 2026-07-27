# payment/serializers.py
from rest_framework import serializers
from .models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'type', 'status', 'amount', 'balance_after', 'auction', 'notes', 'created_at']