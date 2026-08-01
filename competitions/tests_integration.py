from django.test import TestCase
from django.utils import timezone

from competitions.models import Competition, Match, CompetitionEntry
from campaigns.models import Campaign, MarketWindow
from team.models import Team
from competitions import services as competition_services


class CompetitionsIntegrationTests(TestCase):
    def setUp(self):
        # create campaign with small matches_per_market_cycle to trigger market window
        self.campaign = Campaign.objects.create(name='C1', matches_per_market_cycle=1)
        # create a user to be owner and teams linked to campaign
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.owner = User.objects.create_user(username='owner', password='pw', birth_date='2000-01-01', cpf='00000000001', email='owner@example.com')
        self.team_a = Team.objects.create(name='Team A', campaign=self.campaign, owner=self.owner)
        self.owner_b = User.objects.create_user(username='owner2', password='pw', birth_date='1999-01-01', cpf='00000000002', email='owner2@example.com')
        self.team_b = Team.objects.create(name='Team B', campaign=self.campaign, owner=self.owner_b)
        # competition linked to campaign
        self.competition = Competition.objects.create(name='Comp', campaign=self.campaign)
        CompetitionEntry.objects.create(competition=self.competition, team=self.team_a)
        CompetitionEntry.objects.create(competition=self.competition, team=self.team_b)

    def test_simulate_match_opens_market_window(self):
        match = Match.objects.create(competition=self.competition, home_team=self.team_a, away_team=self.team_b)

        # simulate; should call notify_match_played and open market window because matches_per_market_cycle=1
        competition_services.simulate_match(match)

        mw_exists = MarketWindow.objects.filter(campaign=self.campaign).exists()
        self.assertTrue(mw_exists, 'Simulating a match should open a MarketWindow when threshold reached')
