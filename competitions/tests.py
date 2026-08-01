from django.test import TestCase
from django.utils import timezone

from user.models import User
from fifa_data.models import Player
from competitions.models import Competition, Match
from competitions import services as competition_services
from team.services import get_or_create_team
from campaigns.models import Campaign, MarketWindow


class CompetitionsSimulationTests(TestCase):
    def test_simulate_match_and_open_market(self):
        # create campaign with small cycle
        campaign = Campaign.objects.create(name='C1', matches_per_market_cycle=1)

        # create two users and teams with players
        u1 = User.objects.create_user(username='a', email='a@x.com', password='x', cpf='z1', cellphone='', address='', town='', post_code='', country='', birth_date='1990-01-01')
        u2 = User.objects.create_user(username='b', email='b@x.com', password='x', cpf='z2', cellphone='', address='', town='', post_code='', country='', birth_date='1990-01-01')

        t1 = get_or_create_team(u1, campaign)
        t2 = get_or_create_team(u2, campaign)

        p1 = Player.objects.create(fifa_id=4001, common_name='P1', overall_rating=80)
        p2 = Player.objects.create(fifa_id=4002, common_name='P2', overall_rating=70)

        t1.roster_entries.create(player=p1)
        t2.roster_entries.create(player=p2)

        comp = Competition.objects.create(name='Comp', competition_type='league', campaign=campaign)
        match = Match.objects.create(competition=comp, home_team=t1, away_team=t2, played_at=timezone.now())

        # simulate
        match = competition_services.simulate_match(match)

        # scores set
        self.assertIsNotNone(match.home_score)
        self.assertIsNotNone(match.away_score)

        # campaign should have opened a market (matches_per_market_cycle=1)
        mw = MarketWindow.objects.filter(campaign=campaign, is_open=True).first()
        self.assertIsNotNone(mw)
