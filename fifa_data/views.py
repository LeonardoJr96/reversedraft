from django.shortcuts import render
from dj_rql.drf import RQLFilterBackend
from rest_framework import viewsets
from .models import AccelerationType, Player, Club, League, Country, Position, Gender, LeagueType, PlayerPlayStyle, PlayerPlayStylePlus, PlayerPrime, PlayerRole, PlayerRoleAssignment, PlayerSpeciality, PlayerTeam, PlayStyle, PlayStylePlus, Speciality, Stadium, TraitType, FocusType
from .serializers import PlayerSerializer, ClubSerializer, LeagueSerializer, CountrySerializer, PositionSerializer, GenderSerializer, LeagueTypeSerializer, PlayerPlayStyleSerializer, PlayerPlayStylePlusSerializer, PlayerPrimeSerializer, PlayerRoleSerializer, PlayerRoleAssignmentSerializer, PlayerSpecialitySerializer, PlayerTeamSerializer, PlayStyleSerializer, PlayStylePlusSerializer, SpecialitySerializer, StadiumSerializer, TraitTypeSerializer, FocusTypeSerializer, AccelerationTypeSerializer

# Create your views here.
class PlayerViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerSerializer
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

class ClubViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = ClubSerializer
    queryset = Club.objects.all()
    serializer_class = ClubSerializer

class LeagueViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = LeagueSerializer
    queryset = League.objects.all()
    serializer_class = LeagueSerializer

class CountryViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = CountrySerializer
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

class PositionViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PositionSerializer
    queryset = Position.objects.all()
    serializer_class = PositionSerializer

class GenderViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = GenderSerializer
    queryset = Gender.objects.all()
    serializer_class = GenderSerializer

class LeagueTypeViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = LeagueTypeSerializer
    queryset = LeagueType.objects.all()
    serializer_class = LeagueTypeSerializer

class PlayerPlayStyleViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerPlayStyleSerializer
    queryset = PlayerPlayStyle.objects.all()
    serializer_class = PlayerPlayStyleSerializer

class PlayerPlayStylePlusViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerPlayStylePlusSerializer
    queryset = PlayerPlayStylePlus.objects.all()
    serializer_class = PlayerPlayStylePlusSerializer

class PlayerPrimeViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerPrimeSerializer
    queryset = PlayerPrime.objects.all()
    serializer_class = PlayerPrimeSerializer

class PlayerRoleViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerRoleSerializer
    queryset = PlayerRole.objects.all()
    serializer_class = PlayerRoleSerializer

class PlayerRoleAssignmentViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerRoleAssignmentSerializer
    queryset = PlayerRoleAssignment.objects.all()
    serializer_class = PlayerRoleAssignmentSerializer

class PlayerSpecialityViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerSpecialitySerializer
    queryset = PlayerSpeciality.objects.all()
    serializer_class = PlayerSpecialitySerializer

class PlayerTeamViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayerTeamSerializer
    queryset = PlayerTeam.objects.all()
    serializer_class = PlayerTeamSerializer

class PlayStyleViewSet(viewsets.ModelViewSet):
    filter_backends = [RQLFilterBackend]
    rql_filter_class = PlayStyleSerializer
    queryset = PlayStyle.objects.all()
    serializer_class = PlayStyleSerializer

class PlayStylePlusViewSet(viewsets.ModelViewSet):
    queryset = PlayStylePlus.objects.all()
    serializer_class = PlayStylePlusSerializer
    
class SpecialityViewSet(viewsets.ModelViewSet):
    queryset = Speciality.objects.all()
    serializer_class = SpecialitySerializer

class StadiumViewSet(viewsets.ModelViewSet):
    queryset = Stadium.objects.all()
    serializer_class = StadiumSerializer

class TraitTypeViewSet(viewsets.ModelViewSet):
    queryset = TraitType.objects.all()
    serializer_class = TraitTypeSerializer

class FocusTypeViewSet(viewsets.ModelViewSet):
    queryset = FocusType.objects.all()
    serializer_class = FocusTypeSerializer

class AccelerationTypeViewSet(viewsets.ModelViewSet):
    queryset = AccelerationType.objects.all()
    serializer_class = AccelerationTypeSerializer