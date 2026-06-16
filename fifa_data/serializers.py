from rest_framework import serializers
from .models import Player, Club, League, Country, Position, Gender, LeagueType, PlayerPlayStyle, PlayerPlayStylePlus, PlayerPrime, PlayerRole, PlayerRoleAssignment, PlayerSpeciality, PlayerTeam, PlayStyle, PlayStylePlus, Speciality, Stadium, TraitType, FocusType, AccelerationType

class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = '__all__'

class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = '__all__'

class LeagueSerializer(serializers.ModelSerializer):
    class Meta:
        model = League
        fields = '__all__'

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'

class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = '__all__'

class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gender
        fields = '__all__'

class LeagueTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeagueType
        fields = '__all__'

class PlayerPlayStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerPlayStyle
        fields = '__all__'

class PlayerPlayStylePlusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerPlayStylePlus
        fields = '__all__'

class PlayerPrimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerPrime
        fields = '__all__'

class PlayerRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerRole
        fields = '__all__'

class PlayerRoleAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerRoleAssignment
        fields = '__all__'

class PlayerSpecialitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerSpeciality
        fields = '__all__'

class PlayerTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerTeam
        fields = '__all__'

class PlayStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayStyle
        fields = '__all__'

class PlayStylePlusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayStylePlus
        fields = '__all__'

class SpecialitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Speciality
        fields = '__all__'

class StadiumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stadium
        fields = '__all__'

class TraitTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TraitType
        fields = '__all__'

class FocusTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FocusType
        fields = '__all__'

class AccelerationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccelerationType
        fields = '__all__'