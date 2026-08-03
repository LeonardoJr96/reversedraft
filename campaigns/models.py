from django.db import models
from django.conf import settings


class TransferPolicy(models.TextChoices):
    ALWAYS_ALLOWED = 'always_allowed', 'Sempre permitido'
    MARKET_WINDOW_ONLY = 'market_window_only', 'Só durante janela de mercado'


class Campaign(models.Model):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_campaigns')
    # business rules
    min_roster_size = models.PositiveIntegerField(default=18)
    max_roster_size = models.PositiveIntegerField(default=22)
    matches_per_market_cycle = models.PositiveIntegerField(default=3)
    matches_played_since_last_market = models.PositiveIntegerField(default=0)
    transfer_policy = models.CharField(max_length=32, choices=TransferPolicy.choices, default=TransferPolicy.MARKET_WINDOW_ONLY)


class CampaignAdmin(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='admins')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='campaign_adminships')

    class Meta:
        unique_together = ('campaign', 'user')


class CampaignMembership(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='campaign_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('campaign', 'user')


class MarketWindow(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='market_windows')
    name = models.CharField(max_length=255)
    is_open = models.BooleanField(default=False)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    MODE_CHOICES = [
        ('auction', 'Leilão'),
        ('market', 'Mercado direto'),
        ('hybrid', 'Híbrido'),
    ]
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='auction')
    # curation: how many players are shown in this window and whether selection is random
    player_count = models.PositiveIntegerField(null=True, blank=True)
    random_selection = models.BooleanField(default=True)


class MarketListing(models.Model):
    LISTING_TYPE_CHOICES = [
        ('auction', 'Leilão'),
        ('direct', 'Venda direta'),
        ('hybrid', 'Híbrido'),
    ]

    market_window = models.ForeignKey(MarketWindow, on_delete=models.CASCADE, related_name='listings')
    player = models.ForeignKey('fifa_data.Player', on_delete=models.CASCADE, related_name='campaign_listings')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='campaign_listings')
    auction = models.ForeignKey('auction.Auction', on_delete=models.SET_NULL, null=True, blank=True, related_name='campaign_listings')
    listing_type = models.CharField(max_length=20, choices=LISTING_TYPE_CHOICES, default='auction')
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Transfer(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='transfers')
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requested_transfers')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_transfers')
    offered_players = models.ManyToManyField('fifa_data.Player', related_name='offered_transfers', blank=True)
    requested_players = models.ManyToManyField('fifa_data.Player', related_name='requested_transfers', blank=True)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)


class MatchPlayerStat(models.Model):
    match = models.ForeignKey('competitions.Match', on_delete=models.CASCADE, related_name='player_stats')
    player = models.ForeignKey('fifa_data.Player', on_delete=models.CASCADE, related_name='match_stats')
    team = models.ForeignKey('team.Team', on_delete=models.CASCADE, related_name='match_stats', null=True, blank=True)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
