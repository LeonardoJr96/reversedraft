from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.utils import timezone

from common.models import Status
from .models import Transaction, TransactionType, TransactionStatus
from team.services import get_or_create_team
from campaigns.models import MarketListing


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

    # Lê o saldo atual dentro de um atomic com select_for_update para evitar
    # condição de corrida, mas em bloco separado para que o FAILED possa ser
    # persistido mesmo se sairmos por ValidationError.
    with db_transaction.atomic():
        locked_user = user.__class__.objects.select_for_update().get(pk=user.pk)
        balance_snapshot = locked_user.balance

    if balance_snapshot < amount:
        # Registra a tentativa falhada FORA do atomic acima — assim ela não
        # é revertida pelo rollback (que já não existe aqui).
        Transaction.objects.create(
            user=user, auction=auction, type=TransactionType.AUCTION_PAYMENT,
            status=TransactionStatus.FAILED, amount=amount,
            notes="Saldo insuficiente",
        )
        raise ValidationError(f"Saldo insuficiente. Necessário: {amount}, disponível: {balance_snapshot}.")

    # Saldo suficiente: agora sim bloqueia tudo e efetua o pagamento atomicamente.
    with db_transaction.atomic():
        locked_user = user.__class__.objects.select_for_update().get(pk=user.pk)

        # Dupla verificação dentro do segundo lock (outro request pode ter debitado)
        if locked_user.balance < amount:
            Transaction.objects.create(
                user=locked_user, auction=auction, type=TransactionType.AUCTION_PAYMENT,
                status=TransactionStatus.FAILED, amount=amount,
                notes="Saldo insuficiente (segunda verificação)",
            )
            raise ValidationError(f"Saldo insuficiente. Necessário: {amount}, disponível: {locked_user.balance}.")

        locked_user.balance -= amount
        locked_user.save()

        auction.status = Status.PAID
        auction.save()

        # Quando um leilão é pago, registra o jogador no time do vencedor.
        # Se houver uma listagem ativa na campaign para este jogador, usa a campaign
        # da janela de mercado; caso contrário, adiciona ao time global (campaign=None).
        try:
            player = auction.product.player
        except Exception:
            player = None

        campaign = None
        if player is not None:
            listing = MarketListing.objects.filter(player=player, is_active=True).select_related('market_window__campaign').order_by('-pk').first()
            if listing:
                campaign = listing.market_window.campaign

        team = get_or_create_team(locked_user, campaign)
        if player is not None:
            team.roster_entries.get_or_create(player=player)

        return Transaction.objects.create(
            user=locked_user,
            auction=auction,
            type=TransactionType.AUCTION_PAYMENT,
            status=TransactionStatus.COMPLETED,
            amount=amount,
            balance_after=locked_user.balance,
        )