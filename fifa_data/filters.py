from dj_rql.filter_cls import AutoRQLFilterClass, FilterLookup
from .models import Player, Club, League, Country, Position, Gender, LeagueType, PlayerPlayStyle, PlayerPlayStylePlus, PlayerPrime, PlayerRole, PlayerRoleAssignment, PlayerSpeciality, PlayerTeam, PlayStyle, PlayStylePlus, Speciality, Stadium, TraitType, FocusType, AccelerationType

class PlayerFilter(AutoRQLFilterClass):
    MODEL = Player

class ClubFilter(AutoRQLFilterClass):
    MODEL = Club


class LeagueFilter(AutoRQLFilterClass):
    MODEL = League


class CountryFilter(AutoRQLFilterClass):
    MODEL = Country


class PositionFilter(AutoRQLFilterClass):
    MODEL = Position


class GenderFilter(AutoRQLFilterClass):
    MODEL = Gender


class LeagueTypeFilter(AutoRQLFilterClass):
    MODEL = LeagueType


class PlayerPlayStyleFilter(AutoRQLFilterClass):
    MODEL = PlayerPlayStyle


class PlayerPlayStylePlusFilter(AutoRQLFilterClass):
    MODEL = PlayerPlayStylePlus


class PlayerPrimeFilter(AutoRQLFilterClass):
    MODEL = PlayerPrime


class PlayerRoleFilter(AutoRQLFilterClass):
    MODEL = PlayerRole


class PlayerRoleAssignmentFilter(AutoRQLFilterClass):
    MODEL = PlayerRoleAssignment


class PlayerSpecialityFilter(AutoRQLFilterClass):
    MODEL = PlayerSpeciality


class PlayerTeamFilter(AutoRQLFilterClass):
    MODEL = PlayerTeam


class PlayStyleFilter(AutoRQLFilterClass):
    MODEL = PlayStyle


class PlayStylePlusFilter(AutoRQLFilterClass):
    MODEL = PlayStylePlus


class SpecialityFilter(AutoRQLFilterClass):
    MODEL = Speciality


class StadiumFilter(AutoRQLFilterClass):
    MODEL = Stadium


class TraitTypeFilter(AutoRQLFilterClass):
    MODEL = TraitType


class FocusTypeFilter(AutoRQLFilterClass):
    MODEL = FocusType


class AccelerationTypeFilter(AutoRQLFilterClass):
    MODEL = AccelerationType