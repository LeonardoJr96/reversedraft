import math
import random

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import CompetitionEntry, Match
from campaigns.models import MatchPlayerStat
from campaigns import services as campaign_services
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
            team = stat.get('team')
            if team is None:
                raise ValidationError('Time da estatística é obrigatório.')
            if team not in (match.home_team, match.away_team):
                raise ValidationError('Time da estatística não participa desta partida.')
            MatchPlayerStat.objects.create(
                match=match,
                player=stat['player'],
                team=team,
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

    _award_win_credits(match)
    if match.competition.competition_type == 'cup':
        _advance_winner(match)

    # notify campaign that a match was played (may open market window)
    if match.competition and getattr(match.competition, 'campaign', None) is not None:
        campaign_services.notify_match_played(match.competition.campaign)

    return match


def _award_win_credits(match):
    if match.home_score == match.away_score:
        return
    winner = match.home_team if match.home_score > match.away_score else match.away_team
    if winner is None or winner.owner_id is None:
        return
    with transaction.atomic():
        owner = winner.owner.__class__.objects.select_for_update().get(pk=winner.owner_id)
        owner.lance_credits += match.competition.credits_per_win
        owner.save(update_fields=['lance_credits'])


def _advance_winner(match):
    if match.next_match_id is None or match.home_score == match.away_score:
        return
    winner = match.home_team if match.home_score > match.away_score else match.away_team
    next_match = match.next_match
    setattr(next_match, f'{match.next_match_slot}_team', winner)
    next_match.save(update_fields=[f'{match.next_match_slot}_team'])


def finish_competition(competition):
    if not competition.is_active:
        raise ValidationError('Esta competição já foi encerrada.')
    top_entry = competition.entries.order_by('-points', 'id').first()
    if top_entry is None or not competition.matches.filter(status='played').exists():
        raise ValidationError('Nenhuma equipe possui pontuação registrada.')
    if top_entry.team is None or top_entry.team.owner_id is None:
        raise ValidationError('A equipe campeã não possui proprietário.')
    with transaction.atomic():
        competition.is_active = False
        competition.save(update_fields=['is_active'])
        owner = top_entry.team.owner.__class__.objects.select_for_update().get(pk=top_entry.team.owner_id)
        owner.lance_credits += competition.credits_per_title
        owner.save(update_fields=['lance_credits'])
    return {'champion_team_id': top_entry.team_id, 'credits_awarded': competition.credits_per_title}


def generate_bracket(competition, teams):
    if competition.competition_type != 'cup':
        raise ValidationError('Esta competição não é do tipo copa.')
    teams = list(teams)
    if len(teams) < 2:
        raise ValidationError('São necessários pelo menos 2 times para gerar um chaveamento.')
    if competition.matches.exists():
        raise ValidationError('Esta competição já possui partidas no chaveamento.')
    if len({team.id for team in teams}) != len(teams):
        raise ValidationError('Um time não pode aparecer mais de uma vez no chaveamento.')
    random.shuffle(teams)
    size = 2 ** math.ceil(math.log2(len(teams)))
    teams.extend([None] * (size - len(teams)))
    with transaction.atomic():
        first_round = []
        for index in range(0, size, 2):
            home, away = teams[index:index + 2]
            match = Match.objects.create(competition=competition, home_team=home, away_team=away, round_number=1)
            if home is None or away is None:
                match.status = 'played'
                match.home_score, match.away_score = (1, 0) if home else (0, 1)
                match.save(update_fields=['status', 'home_score', 'away_score'])
            first_round.append(match)
        current = first_round
        round_number = 1
        while len(current) > 1:
            round_number += 1
            following = []
            for index in range(0, len(current), 2):
                next_match = Match.objects.create(competition=competition, round_number=round_number)
                for feeder, slot in ((current[index], 'home'), (current[index + 1], 'away')):
                    feeder.next_match = next_match
                    feeder.next_match_slot = slot
                    feeder.save(update_fields=['next_match', 'next_match_slot'])
                following.append(next_match)
            current = following
        for match in first_round:
            if match.status == 'played':
                _advance_winner(match)
        return first_round


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
