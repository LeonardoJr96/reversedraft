from django.db import models
from django.conf import settings


class Competition(models.Model):
    name = models.CharField(max_length=255)
    competition_type = models.CharField(max_length=20, default='league')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # link to campaign so competitions can trigger market windows
    campaign = models.ForeignKey('campaigns.Campaign', on_delete=models.CASCADE, null=True, blank=True, related_name='competitions')
    credits_per_win = models.PositiveIntegerField(default=1)
    credits_per_title = models.PositiveIntegerField(default=5)


class CompetitionEntry(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='entries')
    team = models.ForeignKey('team.Team', on_delete=models.CASCADE, related_name='competition_entries', null=True, blank=True)
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('competition', 'team')


class Match(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Agendado'),
        ('played', 'Jogado'),
    ]

    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='matches')
    home_team = models.ForeignKey('team.Team', on_delete=models.CASCADE, related_name='home_matches', null=True, blank=True)
    away_team = models.ForeignKey('team.Team', on_delete=models.CASCADE, related_name='away_matches', null=True, blank=True)
    home_score = models.IntegerField(default=0)
    away_score = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    played_at = models.DateTimeField(auto_now_add=True)
    round_number = models.PositiveIntegerField(null=True, blank=True)
    next_match = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='feeder_matches')
    next_match_slot = models.CharField(max_length=10, choices=[('home', 'Home'), ('away', 'Away')], null=True, blank=True)
