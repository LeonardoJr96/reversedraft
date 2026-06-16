from dj_rql.filter_cls import AutoRQLFilterClass, FilterLookup
from .models import Player, Club, League, Country, Position, Gender, LeagueType, PlayerPlayStyle, PlayerPlayStylePlus, PlayerPrime, PlayerRole, PlayerRoleAssignment, PlayerSpeciality, PlayerTeam, PlayStyle, PlayStylePlus, Speciality, Stadium, TraitType, FocusType, AccelerationType

class PlayerFilter(AutoRQLFilterClass):
    MODEL = Player

