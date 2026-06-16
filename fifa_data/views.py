from django.shortcuts import render
from dj_rql.drf import RQLFilterBackend
from rest_framework import viewsets

from .models import AccelerationType, Player, Club, League, Country, Position, Gender, LeagueType, PlayerPlayStyle, PlayerPlayStylePlus, PlayerPrime, PlayerRole, PlayerRoleAssignment, PlayerSpeciality, PlayerTeam, PlayStyle, PlayStylePlus, Speciality, Stadium, TraitType, FocusType

from .serializers import PlayerSerializer, ClubSerializer, LeagueSerializer, CountrySerializer, PositionSerializer, GenderSerializer, LeagueTypeSerializer, PlayerPlayStyleSerializer, PlayerPlayStylePlusSerializer, PlayerPrimeSerializer, PlayerRoleSerializer, PlayerRoleAssignmentSerializer, PlayerSpecialitySerializer, PlayerTeamSerializer, PlayStyleSerializer, PlayStylePlusSerializer, SpecialitySerializer, StadiumSerializer, TraitTypeSerializer, FocusTypeSerializer, AccelerationTypeSerializer

from .filters import PlayerFilter, ClubFilter, LeagueFilter, CountryFilter, PositionFilter, GenderFilter, LeagueTypeFilter, PlayerPlayStyleFilter, PlayerPlayStylePlusFilter, PlayerPrimeFilter, PlayerRoleFilter, PlayerRoleAssignmentFilter, PlayerSpecialityFilter, PlayerTeamFilter, PlayStyleFilter, PlayStylePlusFilter, SpecialityFilter, StadiumFilter, TraitTypeFilter, FocusTypeFilter, AccelerationTypeFilter


# Create your views here.
class PlayerViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerFilter
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

class ClubViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = ClubFilter
    queryset = Club.objects.all()
    serializer_class = ClubSerializer

class LeagueViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = LeagueFilter
    queryset = League.objects.all()
    serializer_class = LeagueSerializer

class CountryViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = CountryFilter
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

class PositionViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PositionFilter
    queryset = Position.objects.all()
    serializer_class = PositionSerializer

class GenderViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = GenderFilter
    queryset = Gender.objects.all()
    serializer_class = GenderSerializer

class LeagueTypeViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = LeagueTypeFilter
    queryset = LeagueType.objects.all()
    serializer_class = LeagueTypeSerializer

class PlayerPlayStyleViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerPlayStyleFilter
    queryset = PlayerPlayStyle.objects.all()
    serializer_class = PlayerPlayStyleSerializer

class PlayerPlayStylePlusViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerPlayStylePlusFilter
    queryset = PlayerPlayStylePlus.objects.all()
    serializer_class = PlayerPlayStylePlusSerializer

class PlayerPrimeViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerPrimeFilter
    queryset = PlayerPrime.objects.all()
    serializer_class = PlayerPrimeSerializer

class PlayerRoleViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerRoleFilter
    queryset = PlayerRole.objects.all()
    serializer_class = PlayerRoleSerializer

class PlayerRoleAssignmentViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerRoleAssignmentFilter
    queryset = PlayerRoleAssignment.objects.all()
    serializer_class = PlayerRoleAssignmentSerializer

class PlayerSpecialityViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerSpecialityFilter
    queryset = PlayerSpeciality.objects.all()
    serializer_class = PlayerSpecialitySerializer

class PlayerTeamViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerTeamFilter
    queryset = PlayerTeam.objects.all()
    serializer_class = PlayerTeamSerializer

class PlayStyleViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayStyleFilter
    queryset = PlayStyle.objects.all()
    serializer_class = PlayStyleSerializer

class PlayStylePlusViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayStylePlusFilter
    queryset = PlayStylePlus.objects.all()
    serializer_class = PlayStylePlusSerializer
    
class SpecialityViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = SpecialityFilter
    queryset = Speciality.objects.all()
    serializer_class = SpecialitySerializer

class StadiumViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = StadiumFilter
    queryset = Stadium.objects.all()
    serializer_class = StadiumSerializer

class TraitTypeViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = TraitTypeFilter
    queryset = TraitType.objects.all()
    serializer_class = TraitTypeSerializer

class FocusTypeViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = FocusTypeFilter
    queryset = FocusType.objects.all()
    serializer_class = FocusTypeSerializer

class AccelerationTypeViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = AccelerationTypeFilter
    queryset = AccelerationType.objects.all()
    serializer_class = AccelerationTypeSerializer