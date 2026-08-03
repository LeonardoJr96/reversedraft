from django.core.exceptions import ValidationError

from .models import CompetitionEntry, Match
from campaigns.models import MatchPlayerStat
from campaigns import services as campaign_services
import random
from fifa_data.models import Player
from team.models import RosterEntry


def register_manual_result(match, home_score, away_score, stats=None):
    if match.home_score != 0 or match.away_score != 0 or getattr(match, 'status', None) == 'played':
        raise ValidationError('Este confronto já possui resultado registrado.')

    match.home_score = home_score
    match.away_score = away_score
    match.status = 'played'
    match.save(update_fields=['home_score', 'away_score', 'status'])

    if stats:
        for stat in stats:
            MatchPlayerStat.objects.create(
                match=match,
                player=stat['player'],
                goals=stat.get('goals', 0),
                assists=stat.get('assists', 0),
            )

    entry_home, _ = CompetitionEntry.objects.get_or_create(competition=match.competition, team=match.home_team)
    entry_away, _ = CompetitionEntry.objects.get_or_create(competition=match.competition, team=match.away_team)

    if home_score > away_score:
        entry_home.points += 3
    elif home_score < away_score:
        entry_away.points += 3
    else:
        entry_home.points += 1
        entry_away.points += 1

    entry_home.save(update_fields=['points'])
    entry_away.save(update_fields=['points'])

    # notify campaign that a match was played (may open market window)
    if match.competition and getattr(match.competition, 'campaign', None) is not None:
        campaign_services.notify_match_played(match.competition.campaign)

    return match


def simulate_match(match):
    """Simula um placar para a partida baseada na força média dos jogadores escalados.

    Método simples: força do time = média de `overall_rating` dos jogadores do roster;
    gera gols com ruído Gaussiano em torno de uma expectativa proporcional.
    """
    # calcular força dos times
    def team_strength(team):
        players_qs = RosterEntry.objects.filter(team=team).select_related('player')
        ratings = [p.player.overall_rating or 50 for p in players_qs]
        if not ratings:
            return 50.0
        return sum(ratings) / len(ratings)

    home_strength = team_strength(match.home_team)
    away_strength = team_strength(match.away_team)

    if home_strength + away_strength <= 0:
        home_exp = away_exp = 1.0
    else:
        total = home_strength + away_strength
        home_exp = (home_strength / total) * 3.0
        away_exp = (away_strength / total) * 3.0

    # adicionar ruído e gerar gols inteiros
    home_goals = max(0, int(round(random.gauss(home_exp, 1.2))))
    away_goals = max(0, int(round(random.gauss(away_exp, 1.2))))

    # registrar resultado e disparar efeitos colaterais
    return register_manual_result(match, home_goals, away_goals, stats=None)
