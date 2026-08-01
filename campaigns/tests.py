from django.test import TestCase
from django.utils import timezone

from user.models import User
from fifa_data.models import Player
from campaigns.models import Campaign, MarketListing
from campaigns import services as campaign_services
from team.services import get_or_create_team


class CampaignServicesTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(username='seller', email='s@example.com', password='x', cpf='111', cellphone='', address='', town='', post_code='', country='', birth_date='1990-01-01')
        self.buyer = User.objects.create_user(username='buyer', email='b@example.com', password='x', cpf='222', cellphone='', address='', town='', post_code='', country='', birth_date='1990-01-01')
        self.seller.balance = 0
        self.seller.save()
        self.buyer.balance = 100
        self.buyer.save()

        self.campaign = Campaign.objects.create(name='TestCamp')

    def test_buy_direct_moves_roster_and_transfers_balance(self):
        # create player and seller roster
        player = Player.objects.create(fifa_id=1001, common_name='P1', overall_rating=70, price=30)
        seller_team = get_or_create_team(self.seller, self.campaign)
        seller_team.roster_entries.create(player=player)

        # open market and list player
        window = campaign_services.create_market_window(self.campaign, 'W', starts_at=timezone.now())
        campaign_services.open_market_window(window)
        listing = campaign_services.list_player_for_sale(self.seller, self.campaign, player, listing_type='direct', price=30)

        # perform buy
        buyer_team = campaign_services.buy_direct(self.buyer, self.campaign, player, price=None)

        # reload balances
        self.seller.refresh_from_db()
        self.buyer.refresh_from_db()

        self.assertEqual(float(self.buyer.balance), 70.0)
        self.assertEqual(float(self.seller.balance), 30.0)

        # roster moved
        self.assertFalse(seller_team.roster_entries.filter(player=player).exists())
        self.assertTrue(buyer_team.roster_entries.filter(player=player).exists())

        # listing deactivated
        listing.refresh_from_db()
        self.assertFalse(listing.is_active)

    def test_populate_market_window(self):
        # create several players across different teams
        players = []
        for i in range(4):
            user = User.objects.create_user(username=f'u{i}', email=f'u{i}@ex.com', password='x', cpf=f'cpf{i}', cellphone='', address='', town='', post_code='', country='', birth_date='1990-01-01')
            p = Player.objects.create(fifa_id=2000 + i, common_name=f'P{i}', overall_rating=60 + i, price=10 + i)
            t = get_or_create_team(user, self.campaign)
            t.roster_entries.create(player=p)
            players.append(p)

        window = campaign_services.create_market_window(self.campaign, 'Curated', starts_at=timezone.now(), player_count=2, random_selection=True)

        listings = MarketListing.objects.filter(market_window=window)
        self.assertEqual(listings.count(), 2)

    def test_respond_transfer_swaps_players(self):
        # create two players and teams
        p1 = Player.objects.create(fifa_id=3001, common_name='A', overall_rating=65)
        p2 = Player.objects.create(fifa_id=3002, common_name='B', overall_rating=66)

        user1 = User.objects.create_user(username='u1', email='u1@ex.com', password='x', cpf='c1', cellphone='', address='', town='', post_code='', country='', birth_date='1990-01-01')
        user2 = User.objects.create_user(username='u2', email='u2@ex.com', password='x', cpf='c2', cellphone='', address='', town='', post_code='', country='', birth_date='1990-01-01')
        t1 = get_or_create_team(user1, self.campaign)
        t2 = get_or_create_team(user2, self.campaign)
        t1.roster_entries.create(player=p1)
        t2.roster_entries.create(player=p2)

        transfer = campaign_services.propose_transfer(self.campaign, user1, user2, offered_players=[p1.id], requested_players=[p2.id])
        transfer = campaign_services.respond_transfer(transfer, True, user2)

        # after accepted, players swapped
        self.assertTrue(t1.roster_entries.filter(player=p2).exists())
        self.assertTrue(t2.roster_entries.filter(player=p1).exists())
        self.assertFalse(t1.roster_entries.filter(player=p1).exists())
        self.assertFalse(t2.roster_entries.filter(player=p2).exists())
