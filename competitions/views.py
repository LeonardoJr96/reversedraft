from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Competition, Match
from .serializers import BracketMatchSerializer, CompetitionSerializer, MatchSerializer
from rest_framework.views import APIView
from campaigns import services as campaign_services
from rest_framework.response import Response
from rest_framework import status
from . import services as competition_services
from django.shortcuts import get_object_or_404


class CompetitionListView(generics.ListCreateAPIView):
    queryset = Competition.objects.all()
    serializer_class = CompetitionSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [IsAuthenticated()]


class MatchListView(generics.ListCreateAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

    def post(self, request, *args, **kwargs):
        # Expect home_team and away_team ids; optional home_score/away_score to register
        home_team_id = request.data.get('home_team')
        away_team_id = request.data.get('away_team')
        home_score = request.data.get('home_score')
        away_score = request.data.get('away_score')

        if not home_team_id or not away_team_id:
            return Response({'detail': 'home_team and away_team are required'}, status=status.HTTP_400_BAD_REQUEST)

        from team.models import Team
        home_team = Team.objects.get(pk=home_team_id)
        away_team = Team.objects.get(pk=away_team_id)

        competition = None
        if request.data.get('competition'):
            competition = Competition.objects.get(pk=request.data.get('competition'))

        if competition is not None and getattr(competition, 'campaign', None) is not None:
            try:
                campaign_services._require_admin(request.user, competition.campaign)
            except DjangoValidationError as exc:
                return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)

        match = Match.objects.create(competition=competition, home_team=home_team, away_team=away_team)

        if home_score is not None and away_score is not None:
            try:
                stats = []
                for stat in request.data.get('stats') or []:
                    from fifa_data.models import Player
                    from team.models import Team
                    stats.append({
                        'player': Player.objects.get(pk=stat['player']),
                        'team': Team.objects.get(pk=stat['team']),
                        'goals': stat.get('goals', 0),
                        'assists': stat.get('assists', 0),
                    })
                match = competition_services.register_manual_result(match, int(home_score), int(away_score), stats=stats)
            except DjangoValidationError as exc:
                return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(MatchSerializer(match).data, status=status.HTTP_201_CREATED)


class SimulateMatchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        match = get_object_or_404(Match, pk=pk)
        if match.competition and getattr(match.competition, 'campaign', None) is not None:
            try:
                campaign_services._require_admin(request.user, match.competition.campaign)
            except DjangoValidationError as exc:
                return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)

        try:
            match = competition_services.simulate_match(match)
        except DjangoValidationError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(MatchSerializer(match).data, status=status.HTTP_200_OK)


class FinishCompetitionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        competition = get_object_or_404(Competition, pk=pk)
        try:
            if competition.campaign_id:
                campaign_services._require_admin(request.user, competition.campaign)
            elif not request.user.is_staff:
                return Response({'detail': 'Apenas administradores podem encerrar esta competição.'}, status=status.HTTP_403_FORBIDDEN)
            return Response(competition_services.finish_competition(competition))
        except DjangoValidationError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class GenerateBracketView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        competition = get_object_or_404(Competition, pk=pk)
        try:
            if competition.campaign_id:
                campaign_services._require_admin(request.user, competition.campaign)
            elif not request.user.is_staff:
                return Response({'detail': 'Apenas administradores podem gerar o chaveamento.'}, status=status.HTTP_403_FORBIDDEN)
            from team.models import Team
            teams = list(Team.objects.filter(pk__in=request.data.get('team_ids', [])))
            if len(teams) != len(request.data.get('team_ids', [])):
                return Response({'detail': 'Um ou mais times não foram encontrados.'}, status=status.HTTP_400_BAD_REQUEST)
            matches = competition_services.generate_bracket(competition, teams)
            return Response({'matches': BracketMatchSerializer(matches, many=True).data}, status=status.HTTP_201_CREATED)
        except DjangoValidationError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class BracketView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        competition = get_object_or_404(Competition, pk=pk)
        rounds = []
        for round_number in competition.matches.exclude(round_number__isnull=True).values_list('round_number', flat=True).distinct().order_by('round_number'):
            matches = competition.matches.filter(round_number=round_number).select_related('home_team', 'away_team', 'next_match')
            rounds.append({'round_number': round_number, 'matches': BracketMatchSerializer(matches, many=True).data})
        return Response({'rounds': rounds})
