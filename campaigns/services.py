from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth import get_user_model

from auction.services import create_auction
from fifa_data.models import Player
from products.models import Product
from team.models import Team
from team.services import get_or_create_team
from .models import Campaign, CampaignAdmin, CampaignMembership, MarketListing, MarketWindow, Transfer
from payment.models import Transaction, TransactionType, TransactionStatus
from payment.services import recharge_balance
import random


def is_campaign_admin(user, campaign):
    return CampaignAdmin.objects.filter(campaign=campaign, user=user).exists()


def _require_admin(user, campaign):
    if not is_campaign_admin(user, campaign):
        raise ValidationError('Você precisa ser administrador da campanha.')


def get_or_create_campaign_team(user, campaign):
    team, _ = Team.objects.get_or_create(owner=user, campaign=campaign)
    return team


def roster_size(team):
    return team.roster_entries.count()


def create_campaign(user, name, **kwargs):
    with transaction.atomic():
        campaign = Campaign.objects.create(created_by=user, name=name, **kwargs)
        CampaignAdmin.objects.get_or_create(campaign=campaign, user=user)
        CampaignMembership.objects.get_or_create(campaign=campaign, user=user)
        return campaign


def add_campaign_admin(actor, campaign, target_user):
    _require_admin(actor, campaign)
    if target_user.pk == actor.pk:
        raise ValidationError('O criador já é administrador.')
    CampaignAdmin.objects.get_or_create(campaign=campaign, user=target_user)
    CampaignMembership.objects.get_or_create(campaign=campaign, user=target_user)
    return campaign


def remove_campaign_admin(actor, campaign, target_user):
    _require_admin(actor, campaign)
    CampaignAdmin.objects.filter(campaign=campaign, user=target_user).delete()
    return campaign


def join_campaign(user, campaign):
    CampaignMembership.objects.get_or_create(campaign=campaign, user=user)
    return campaign


def _validate_roster_limits(team, campaign, expected_delta=0):
    current_size = team.roster_entries.count() + expected_delta
    if current_size < campaign.min_roster_size:
        raise ValidationError(f'O elenco não pode ficar abaixo de {campaign.min_roster_size} jogadores.')
    if current_size > campaign.max_roster_size:
        raise ValidationError(f'O elenco não pode ultrapassar {campaign.max_roster_size} jogadores.')


def _transfers_allowed_now(campaign):
    if campaign.transfer_policy == 'always_allowed':
        return True
    if campaign.transfer_policy == 'market_window_only':
        return MarketWindow.objects.filter(campaign=campaign, is_open=True).exists()
    return False


def release_player(user, campaign, player):
    team = get_or_create_campaign_team(user, campaign)
    if team.roster_entries.filter(player=player).count() == 0:
        raise ValidationError('Este jogador não está no seu elenco da campanha.')
    if team.roster_entries.count() - 1 < campaign.min_roster_size:
        raise ValidationError(f'Você não pode dispensar este jogador porque o elenco já está no limite mínimo de {campaign.min_roster_size}.')
    team.roster_entries.filter(player=player).delete()
    return team


def list_player_for_sale(user, campaign, player, listing_type='auction', price=None):
    team = get_or_create_campaign_team(user, campaign)
    if not team.roster_entries.filter(player=player).exists():
        raise ValidationError('Este jogador não está no seu elenco da campanha.')

    if team.roster_entries.count() - 1 < campaign.min_roster_size:
        raise ValidationError(f'Você não pode colocar este jogador à venda porque o elenco já está no limite mínimo de {campaign.min_roster_size}.')

    window = MarketWindow.objects.filter(campaign=campaign, is_open=True).order_by('-pk').first()
    if window is None:
        raise ValidationError('Não existe janela de mercado aberta.')

    listing = MarketListing.objects.create(
        market_window=window,
        player=player,
        seller=user,
        listing_type=listing_type,
        price=price,
        is_active=True,
    )
    return listing


def withdraw_listing(user, campaign, listing_id):
    listing = MarketListing.objects.get(id=listing_id, market_window__campaign=campaign)
    if listing.seller_id != user.id and not is_campaign_admin(user, campaign):
        raise ValidationError('Você não pode remover esta listagem.')
    listing.is_active = False
    listing.save(update_fields=['is_active'])
    return listing


def create_market_window(campaign, name, starts_at=None, ends_at=None, mode='auction', player_count=None, random_selection=True, per_player_mode=None):
    """Cria uma janela de mercado com opções de modo e curadoria.

    - `mode`: 'auction' | 'market' | 'hybrid'
    - `player_count`: quantos jogadores serão incluídos (None = sem limitação)
    - `random_selection`: se True, seleciona aleatoriamente os jogadores quando curadoria for aplicada
    """
    window = MarketWindow.objects.create(
        campaign=campaign,
        name=name,
        starts_at=starts_at,
        ends_at=ends_at,
        mode=mode,
        player_count=player_count,
        random_selection=random_selection,
    )
    if player_count:
        populate_market_window(window, per_player_mode=per_player_mode)
    return window


def populate_market_window(window, per_player_mode=None):
    """Pre-popula a janela de mercado com `player_count` jogadores extraídos dos
    elencos da campanha. Seleção aleatória quando `random_selection=True`.
    Cria `MarketListing` com `listing_type` igual a `window.mode` (mapping).
    """
    if not window.player_count:
        return []
    per_player_mode = per_player_mode or {}

    campaign = window.campaign
    # obter todos os jogadores presentes nos elencos da campanha
    from team.models import RosterEntry

    qs = RosterEntry.objects.filter(team__campaign=campaign).select_related('player', 'team__owner')
    players = []
    for r in qs:
        # skip players already listed in active listings
        already = MarketListing.objects.filter(player=r.player, market_window=window).exists()
        if not already:
            players.append((r.player, r.team.owner))

    if not players:
        return []

    if window.random_selection:
        selected = random.sample(players, min(len(players), window.player_count))
    else:
        selected = players[: window.player_count]

    created = []
    for player, seller in selected:
        listing_type = per_player_mode.get(player.id, per_player_mode.get(str(player.id)))
        if listing_type is None:
            listing_type = 'auction' if window.mode == 'auction' else 'direct' if window.mode == 'market' else 'hybrid'
        if listing_type not in {'auction', 'direct'}:
            raise ValidationError('Modalidade individual deve ser auction ou direct.')
        listing = MarketListing.objects.create(
            market_window=window,
            player=player,
            seller=seller,
            listing_type=listing_type,
            price=player.price if player.price is not None else None,
            is_active=True,
        )
        created.append(listing)

    return created


def update_listing_type(actor, listing, listing_type):
    if listing_type not in {'auction', 'direct'}:
        raise ValidationError('Modalidade deve ser auction ou direct.')
    _require_admin(actor, listing.market_window.campaign)
    if listing.auction_id is not None:
        raise ValidationError('Não é possível alterar a modalidade após a janela ser aberta.')
    listing.listing_type = listing_type
    listing.save(update_fields=['listing_type'])
    return listing


def open_market_window(window):
    with transaction.atomic():
        window = MarketWindow.objects.select_for_update().get(pk=window.pk)
        window.is_open = True
        window.save(update_fields=['is_open'])

        for listing in MarketListing.objects.filter(market_window=window, is_active=True, listing_type__in=['auction', 'hybrid'], auction__isnull=True):
            product, _ = Product.objects.get_or_create(
                player=listing.player,
                defaults={
                    'title': listing.player.common_name or listing.player.fifa_id,
                    'description': f'Jogador do mercado da campanha {window.campaign.name}',
                    'price': listing.player.price or 0,
                },
            )
            auction = create_auction(product=product, pricing_mode='player_value', duration_minutes=60, manual_price=None)
            listing.auction = auction
            listing.save(update_fields=['auction'])

        return window


def close_market_window(window):
    window.is_open = False
    window.save(update_fields=['is_open'])
    return window


def notify_match_played(campaign):
    """Called when a match in a campaign finishes. Increments the counter and
    opens a market window automatically when matches_per_market_cycle is reached.
    """
    with transaction.atomic():
        c = Campaign.objects.select_for_update().get(pk=campaign.pk)
        c.matches_played_since_last_market += 1
        if c.matches_played_since_last_market >= c.matches_per_market_cycle:
            # reset counter and open a new market window
            c.matches_played_since_last_market = 0
            c.save(update_fields=['matches_played_since_last_market'])
            now = timezone.now()
            window = create_market_window(c, name=f'Auto market after {c.matches_per_market_cycle} matches', starts_at=now, ends_at=now + timedelta(days=1), mode='market')
            open_market_window(window)
        else:
            c.save(update_fields=['matches_played_since_last_market'])
    return c


def buy_direct(user, campaign, player, price):
    # Compra direta: valida existência de uma MarketListing ativa (direct|hybrid),
    # bloqueia buyer/seller/listing, transfere saldo, move o RosterEntry e registra Transaction.
    listing = MarketListing.objects.filter(
        market_window__campaign=campaign,
        player=player,
        is_active=True,
        listing_type__in=['direct', 'hybrid'],
    ).order_by('-pk').first()

    if listing is None:
        raise ValidationError('Este jogador não está disponível para compra direta.')

    # Use transaction to avoid races
    with transaction.atomic():
        # lock listing and users
        listing = MarketListing.objects.select_for_update().get(pk=listing.pk)
        buyer = user.__class__.objects.select_for_update().get(pk=user.pk)
        seller = user.__class__.objects.select_for_update().get(pk=listing.seller_id)

        # determine price to charge
        listing_price = listing.price
        if listing_price is None:
            raise ValidationError('Esta listagem não tem preço definido para compra direta.')

        if price is None:
            charge = listing_price
        else:
            charge = price

        if charge != listing_price:
            raise ValidationError('O valor informado não corresponde ao preço da listagem.')

        if buyer.balance < charge:
            # criar transação de falha para histórico
            Transaction.objects.create(
                user=buyer,
                auction=None,
                type=TransactionType.DIRECT_PURCHASE,
                status=TransactionStatus.FAILED,
                amount=charge,
                balance_after=buyer.balance,
                notes='Saldo insuficiente para compra direta',
            )
            raise ValidationError('Saldo insuficiente.')

        # verifica que o vendedor realmente tem o jogador no roster da campanha
        seller_team = get_or_create_campaign_team(seller, campaign)
        if not seller_team.roster_entries.filter(player=player).exists():
            raise ValidationError('Vendedor não possui este jogador no elenco da campanha.')

        buyer_team = get_or_create_campaign_team(buyer, campaign)
        _validate_roster_limits(buyer_team, campaign, expected_delta=1)
        _validate_roster_limits(seller_team, campaign, expected_delta=-1)

        # efetiva transferências de saldo
        buyer.balance -= charge
        buyer.save(update_fields=['balance'])

        seller.balance += charge
        seller.save(update_fields=['balance'])

        # registra transação do comprador
        Transaction.objects.create(
            user=buyer,
            auction=None,
            type=TransactionType.DIRECT_PURCHASE,
            status=TransactionStatus.COMPLETED,
            amount=charge,
            balance_after=buyer.balance,
            notes=f'Compra direta: {player.id} na campanha {campaign.id}',
        )

        # move roster entry do vendedor para o comprador
        # remove do vendedor
        seller_team.roster_entries.filter(player=player).delete()
        # adiciona ao comprador
        buyer_team.roster_entries.get_or_create(player=player)

        # desativa a listagem
        listing.is_active = False
        listing.save(update_fields=['is_active'])

    return buyer_team


def propose_transfer(campaign, requester, receiver, offered_players=None, requested_players=None):
    """Cria uma proposta de troca onde `requester` oferece `offered_players`
    e solicita `requested_players` do `receiver`.
    Os argumentos podem ser listas de `Player` instances ou de ids.
    """
    if not _transfers_allowed_now(campaign):
        raise ValidationError('As transferências não estão permitidas neste momento para esta campanha.')

    transfer = Transfer.objects.create(
        campaign=campaign,
        requester=requester,
        receiver=receiver,
        status='pending',
    )

    if offered_players:
        transfer.offered_players.add(*[p.id if hasattr(p, 'id') else p for p in offered_players])
    if requested_players:
        transfer.requested_players.add(*[p.id if hasattr(p, 'id') else p for p in requested_players])

    return transfer


def respond_transfer(transfer, accepted, responder):
    if transfer.status != 'pending':
        raise ValidationError('Esta proposta não está pendente.')

    if responder.id not in {transfer.requester_id, transfer.receiver_id}:
        raise ValidationError('Você não participa desta proposta.')

    if not accepted:
        transfer.status = 'rejected'
        transfer.save(update_fields=['status'])
        return transfer

    # accepted path
    if not _transfers_allowed_now(transfer.campaign):
        raise ValidationError('As transferências não estão permitidas neste momento para esta campanha.')

    offered = list(transfer.offered_players.all())
    requested = list(transfer.requested_players.all())

    with transaction.atomic():
        # lock the teams to avoid races
        requester_team = get_or_create_campaign_team(transfer.requester, transfer.campaign)
        receiver_team = get_or_create_campaign_team(transfer.receiver, transfer.campaign)
        # lock team rows
        from team.models import Team as TeamModel
        TeamModel.objects.select_for_update().get(pk=requester_team.pk)
        TeamModel.objects.select_for_update().get(pk=receiver_team.pk)

        # validate ownership
        missing = []
        for p in offered:
            if not requester_team.roster_entries.filter(player=p).exists():
                missing.append((transfer.requester, p))
        for p in requested:
            if not receiver_team.roster_entries.filter(player=p).exists():
                missing.append((transfer.receiver, p))

        if missing:
            raise ValidationError('Um ou mais jogadores não estão disponíveis nos elencos correspondentes.')

        requester_size_after = requester_team.roster_entries.count() - len(offered) + len(requested)
        receiver_size_after = receiver_team.roster_entries.count() - len(requested) + len(offered)
        if requester_size_after < transfer.campaign.min_roster_size or requester_size_after > transfer.campaign.max_roster_size:
            raise ValidationError('A troca deixaria um dos elencos fora do limite permitido.')
        if receiver_size_after < transfer.campaign.min_roster_size or receiver_size_after > transfer.campaign.max_roster_size:
            raise ValidationError('A troca deixaria um dos elencos fora do limite permitido.')

        # perform transfers: offered -> receiver; requested -> requester
        for p in offered:
            requester_team.roster_entries.filter(player=p).delete()
            receiver_team.roster_entries.get_or_create(player=p)

        for p in requested:
            receiver_team.roster_entries.filter(player=p).delete()
            requester_team.roster_entries.get_or_create(player=p)

        transfer.status = 'accepted'
        transfer.save(update_fields=['status'])

    return transfer
