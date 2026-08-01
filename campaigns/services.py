from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from fifa_data.models import Player
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


def release_player(user, campaign, player):
    team = get_or_create_campaign_team(user, campaign)
    team.roster_entries.filter(player=player).delete()
    return team


def list_player_for_sale(user, campaign, player, listing_type='auction', price=None):
    team = get_or_create_campaign_team(user, campaign)
    if not team.roster_entries.filter(player=player).exists():
        raise ValidationError('Este jogador não está no seu elenco da campanha.')

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


def create_market_window(campaign, name, starts_at=None, ends_at=None, mode='auction', player_count=None, random_selection=True):
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
        populate_market_window(window)
    return window


def populate_market_window(window):
    """Pre-popula a janela de mercado com `player_count` jogadores extraídos dos
    elencos da campanha. Seleção aleatória quando `random_selection=True`.
    Cria `MarketListing` com `listing_type` igual a `window.mode` (mapping).
    """
    if not window.player_count:
        return []

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
        listing = MarketListing.objects.create(
            market_window=window,
            player=player,
            seller=seller,
            listing_type='auction' if window.mode == 'auction' else 'direct' if window.mode == 'market' else 'hybrid',
            price=player.price if player.price is not None else None,
            is_active=True,
        )
        created.append(listing)

    return created


def open_market_window(window):
    window.is_open = True
    window.save(update_fields=['is_open'])
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
        buyer_team = get_or_create_campaign_team(buyer, campaign)
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
