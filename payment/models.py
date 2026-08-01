from django.db import models


class TransactionType(models.TextChoices):
    AUCTION_PAYMENT = "auction_payment", "Pagamento de leilão"
    BALANCE_RECHARGE = "balance_recharge", "Recarga de saldo"
    REFUND = "refund", "Estorno"
    DIRECT_PURCHASE = "direct_purchase", "Compra direta (mercado P2P)"


class TransactionStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    COMPLETED = "completed", "Concluída"
    FAILED = "failed", "Falhou"


class Transaction(models.Model):
    user = models.ForeignKey(
        'user.User', on_delete=models.CASCADE, related_name='transactions'
    )
    auction = models.ForeignKey(
        'auction.Auction', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transactions',
        help_text="Preenchido só em transações do tipo auction_payment",
    )
    type = models.CharField(max_length=20, choices=TransactionType.choices)
    status = models.CharField(max_length=20, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Sempre positivo — o sinal é dado pelo 'type'")
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_type_display()} - {self.user} - {self.amount}"