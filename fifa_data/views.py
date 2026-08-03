from django.shortcuts import render
from dj_rql.drf import RQLFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings

from .models import AccelerationType, Player, Club, League, Country, Position, Gender, LeagueType, PlayerPlayStyle, PlayerPlayStylePlus, PlayerPrime, PlayerRole, PlayerRoleAssignment, PlayerSpeciality, PlayerTeam, PlayStyle, PlayStylePlus, Speciality, Stadium, TraitType, FocusType
from .serializers import PlayerSerializer, ClubSerializer, LeagueSerializer, CountrySerializer, PositionSerializer, GenderSerializer, LeagueTypeSerializer, PlayerPlayStyleSerializer, PlayerPlayStylePlusSerializer, PlayerPrimeSerializer, PlayerRoleSerializer, PlayerRoleAssignmentSerializer, PlayerSpecialitySerializer, PlayerTeamSerializer, PlayStyleSerializer, PlayStylePlusSerializer, SpecialitySerializer, StadiumSerializer, TraitTypeSerializer, FocusTypeSerializer, AccelerationTypeSerializer
from .filters import PlayerFilter, ClubFilter, LeagueFilter, CountryFilter, PositionFilter, GenderFilter, LeagueTypeFilter, PlayerPlayStyleFilter, PlayerPlayStylePlusFilter, PlayerPrimeFilter, PlayerRoleFilter, PlayerRoleAssignmentFilter, PlayerSpecialityFilter, PlayerTeamFilter, PlayStyleFilter, PlayStylePlusFilter, SpecialityFilter, StadiumFilter, TraitTypeFilter, FocusTypeFilter, AccelerationTypeFilter
from .services import import_players_bulk


class AdminWriteModelViewSet(viewsets.ModelViewSet):
    """Dados de referência são públicos para leitura; alterações exigem staff."""
    def get_permissions(self):
        return [AllowAny()] if self.action in {"list", "retrieve"} else [IsAdminUser()]

class PlayerViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerFilter
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

class ClubViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = ClubFilter
    queryset = Club.objects.all()
    serializer_class = ClubSerializer

class LeagueViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = LeagueFilter
    queryset = League.objects.all()
    serializer_class = LeagueSerializer

class CountryViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = CountryFilter
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

class PositionViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PositionFilter
    queryset = Position.objects.all()
    serializer_class = PositionSerializer

class GenderViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = GenderFilter
    queryset = Gender.objects.all()
    serializer_class = GenderSerializer

class LeagueTypeViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = LeagueTypeFilter
    queryset = LeagueType.objects.all()
    serializer_class = LeagueTypeSerializer

class PlayerPlayStyleViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerPlayStyleFilter
    queryset = PlayerPlayStyle.objects.all()
    serializer_class = PlayerPlayStyleSerializer

class PlayerPlayStylePlusViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerPlayStylePlusFilter
    queryset = PlayerPlayStylePlus.objects.all()
    serializer_class = PlayerPlayStylePlusSerializer

class PlayerPrimeViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerPrimeFilter
    queryset = PlayerPrime.objects.all()
    serializer_class = PlayerPrimeSerializer

class PlayerRoleViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerRoleFilter
    queryset = PlayerRole.objects.all()
    serializer_class = PlayerRoleSerializer

class PlayerRoleAssignmentViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerRoleAssignmentFilter
    queryset = PlayerRoleAssignment.objects.all()
    serializer_class = PlayerRoleAssignmentSerializer

class PlayerSpecialityViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerSpecialityFilter
    queryset = PlayerSpeciality.objects.all()
    serializer_class = PlayerSpecialitySerializer

class PlayerTeamViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerTeamFilter
    queryset = PlayerTeam.objects.all()
    serializer_class = PlayerTeamSerializer

class PlayStyleViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayStyleFilter
    queryset = PlayStyle.objects.all()
    serializer_class = PlayStyleSerializer

class PlayStylePlusViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayStylePlusFilter
    queryset = PlayStylePlus.objects.all()
    serializer_class = PlayStylePlusSerializer

class SpecialityViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = SpecialityFilter
    queryset = Speciality.objects.all()
    serializer_class = SpecialitySerializer

class StadiumViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = StadiumFilter
    queryset = Stadium.objects.all()
    serializer_class = StadiumSerializer

class TraitTypeViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = TraitTypeFilter
    queryset = TraitType.objects.all()
    serializer_class = TraitTypeSerializer

class FocusTypeViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = FocusTypeFilter
    queryset = FocusType.objects.all()
    serializer_class = FocusTypeSerializer

class AccelerationTypeViewSet(AdminWriteModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = AccelerationTypeFilter
    queryset = AccelerationType.objects.all()
    serializer_class = AccelerationTypeSerializer


class PlayerBulkImportView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if request.headers.get("X-Scraper-Key") != settings.SCRAPER_IMPORT_KEY:
            return Response({"detail": "chave inválida"}, status=401)
        rows = request.data.get("players", [])
        players = import_players_bulk(rows)
        return Response({"imported": len(players)}, status=201)