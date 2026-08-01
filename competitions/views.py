from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import Competition, Match
from .serializers import CompetitionSerializer, MatchSerializer
from rest_framework.views import APIView
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

        match = Match.objects.create(competition_id=request.data.get('competition'), home_team=home_team, away_team=away_team)

        if home_score is not None and away_score is not None:
            match = competition_services.register_manual_result(match, int(home_score), int(away_score), stats=request.data.get('stats'))

        return Response(MatchSerializer(match).data, status=status.HTTP_201_CREATED)


class SimulateMatchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        match = get_object_or_404(Match, pk=pk)
        match = competition_services.simulate_match(match)
        return Response(MatchSerializer(match).data, status=status.HTTP_200_OK)
