from django.urls import path, include
from rest_framework.routers import DefaultRouter
from fifa_data.views import PlayerViewSet, ClubViewSet, LeagueViewSet, CountryViewSet, PositionViewSet, GenderViewSet, LeagueTypeViewSet, PlayerPlayStyleViewSet, PlayerPlayStylePlusViewSet, PlayerPrimeViewSet, PlayerRoleViewSet, PlayerRoleAssignmentViewSet, PlayerSpecialityViewSet, PlayerTeamViewSet, PlayStyleViewSet, PlayStylePlusViewSet, SpecialityViewSet, StadiumViewSet, TraitTypeViewSet, FocusTypeViewSet, AccelerationTypeViewSet

router = DefaultRouter()

router.register(r'players', PlayerViewSet)
router.register(r'clubs', ClubViewSet)
router.register(r'leagues', LeagueViewSet)
router.register(r'countries', CountryViewSet)
router.register(r'positions', PositionViewSet)
router.register(r'genders', GenderViewSet)
router.register(r'league_types', LeagueTypeViewSet)
router.register(r'player_play_styles', PlayerPlayStyleViewSet)
router.register(r'player_play_styles_plus', PlayerPlayStylePlusViewSet)
router.register(r'player_primes', PlayerPrimeViewSet)
router.register(r'player_roles', PlayerRoleViewSet)
router.register(r'player_role_assignments', PlayerRoleAssignmentViewSet)
router.register(r'player_specialities', PlayerSpecialityViewSet)
router.register(r'player_teams', PlayerTeamViewSet) 
router.register(r'play_styles', PlayStyleViewSet)
router.register(r'play_styles_plus', PlayStylePlusViewSet)
router.register(r'specialities', SpecialityViewSet)
router.register(r'stadiums', StadiumViewSet)
router.register(r'trait_types', TraitTypeViewSet)
router.register(r'focus_types', FocusTypeViewSet)
router.register(r'acceleration_types', AccelerationTypeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]