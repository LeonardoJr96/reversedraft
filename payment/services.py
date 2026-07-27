from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.utils import timezone

from common.models import Status
from .models import Transaction, TransactionType, TransactionStatus


def recharge_balance(user, amount) -> Transaction:
    if amount <= 0:
        raise ValidationError("O valor de recarga deve ser positivo.")

    with db_transaction.atomic():
        locked_user = user.__class__.objects.select_for_update().get(pk=user.pk)
        locked_user.balance += amount
        locked_user.save()

        return Transaction.objects.create(
            user=locked_user,
            type=TransactionType.BALANCE_RECHARGE,
            status=TransactionStatus.COMPLETED,
            amount=amount,
            balance_after=locked_user.balance,
        )


def pay_for_auction(user, auction) -> Transaction:
    """Paga um leilão ganho (Auction.status == PENDING, Auction.winner == user)."""
    if auction.winner_id != user.id:
        raise ValidationError("Você não é o vencedor deste leilão.")

    if auction.status != Status.PENDING:
        raise ValidationError("Este leilão não está aguardando pagamento.")

    if auction.payment_deadline and auction.payment_deadline < timezone.now():
        raise ValidationError("O prazo de pagamento deste leilão expirou.")

    winning_bid = auction.bids.order_by('-price', 'bid_time').first()
    if winning_bid is None:
        raise ValidationError("Leilão sem lance vencedor — não há valor a pagar.")

    amount = winning_bid.price

    with db_transaction.atomic():
        locked_user = user.__class__.objects.select_for_update().get(pk=user.pk)

        if locked_user.balance < amount:
            txn = Transaction.objects.create(
                user=locked_user, auction=auction, type=TransactionType.AUCTION_PAYMENT,
                status=TransactionStatus.FAILED, amount=amount,
                notes="Saldo insuficiente",
            )
            raise ValidationError(f"Saldo insuficiente. Necessário: {amount}, disponível: {locked_user.balance}.")

        locked_user.balance -= amount
        locked_user.save()

        auction.status = Status.PAID
        auction.save()

        return Transaction.objects.create(
            user=locked_user,
            auction=auction,
            type=TransactionType.AUCTION_PAYMENT,
            status=TransactionStatus.COMPLETED,
            amount=amount,
            balance_after=locked_user.balance,
        )