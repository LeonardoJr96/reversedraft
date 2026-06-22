from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .choices import STATUS_CHOICES
from collection.models import UserCard  # ajuste para o nome real do seu app de collection
from fifa_data.models import Player  # ajuste para o app real dos cards


class Auction(models.Model):
    user_card = models.ForeignKey(
        UserCard,
        on_delete=models.CASCADE,
        related_name='auctions',
        verbose_name=_("Card"),
        help_text=_("Instância específica da carta sendo leiloada"),
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='auctions',
        verbose_name=_("Seller"),
    )
    starting_bid = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Starting Bid"))
    current_bid = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_("Current Bid"))
    highest_bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='auctions_winning',
        verbose_name=_("Highest Bidder"),
    )
    end_time = models.DateTimeField(verbose_name=_("End Time"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_("Status"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    @property
    def is_active(self):
        from django.utils import timezone
        return self.end_time > timezone.now() and self.status == 'pending'

    def __str__(self):
        return f"Auction of {self.user_card.player} by {self.seller.username}"

    class Meta:
        verbose_name = _("Auction")
        verbose_name_plural = _("Auctions")
        ordering = ['-created_at']
        constraints = [
            # Impede que a mesma carta tenha dois leilões pendentes ao mesmo tempo.
            # Reforça (no banco) o que o is_locked do UserCard já controla na aplicação.
            models.UniqueConstraint(
                fields=['user_card'],
                condition=models.Q(status='pending'),
                name='uq_user_card_pending_auction',
            ),
        ]


class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids', verbose_name=_("Auction"))
    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='auction_bids',
        verbose_name=_("Bidder"),
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Amount"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    def __str__(self):
        return f"{self.bidder.username} bid {self.amount} on {self.auction.user_card.player}"

    class Meta:
        verbose_name = _("Bid")
        verbose_name_plural = _("Bids")
        ordering = ['-amount']


# ============================================================
# SORTEIO PRÉVIO AO LEILÃO
# ============================================================

class RandomCardPool(models.Model):
    """
    Pool de jogadores candidatos a sorteio pra leilão.
    Quando um candidato é sorteado mas não escolhido, ele volta pro
    status 'available' e pode reaparecer num sorteio futuro — não é descartado.
    """

    STATUS_CHOICES = [
        ('available', _('Disponível')),
        ('drawn', _('Sorteado (aguardando escolha)')),
        ('used', _('Usado em leilão')),
    ]

    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='pool_entries',
        verbose_name=_("Player"),
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='available', verbose_name=_("Status")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        db_table = "random_card_pool"
        verbose_name = _("Random Card Pool Entry")
        verbose_name_plural = _("Random Card Pool Entries")

    def __str__(self):
        return f"{self.player} ({self.get_status_display()})"


class AuctionDraw(models.Model):
    """
    Rodada de sorteio: o dono do leilão recebe N candidatos aleatórios
    (RandomCardPool) e tem até `expires_at` pra escolher um deles.

    Fluxo (lógica de serviço, a implementar):
    1. Sorteia N entradas com status='available' do pool, marca como 'drawn'
       e associa em `candidates`.
    2. Dono escolhe uma -> cria UserCard(owner=dono, player=candidata.player) ->
       cria Auction(user_card=..., seller=dono, ...) -> liga em `auction`.
    3. A candidata escolhida vira status='used'; as demais voltam pra 'available'.
    4. Se `expires_at` passar sem escolha, status='expired' e todas as
       candidatas voltam pra 'available'.
    """

    STATUS_CHOICES = [
        ('pending', _('Aguardando escolha')),
        ('completed', _('Concluído')),
        ('expired', _('Expirado sem escolha')),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='auction_draws',
        verbose_name=_("Owner"),
        help_text=_("Quem vai escolher entre os candidatos sorteados"),
    )
    candidates = models.ManyToManyField(
        RandomCardPool,
        related_name='draws',
        verbose_name=_("Candidates"),
    )
    chosen_candidate = models.ForeignKey(
        RandomCardPool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chosen_in',
        verbose_name=_("Chosen Candidate"),
    )
    auction = models.OneToOneField(
        Auction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='draw',
        verbose_name=_("Resulting Auction"),
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_("Status")
    )
    expires_at = models.DateTimeField(verbose_name=_("Expires At"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        db_table = "auction_draws"
        verbose_name = _("Auction Draw")
        verbose_name_plural = _("Auction Draws")
        ordering = ['-created_at']

    @property
    def is_open(self):
        from django.utils import timezone
        return self.status == 'pending' and self.expires_at > timezone.now()

    def __str__(self):
        return f"Draw de {self.owner.username} ({self.get_status_display()})"

# Create your models here.