import base64
from rest_framework import serializers
from .models import Player, Club, League, Country, Position, Gender, LeagueType, PlayerPlayStyle, PlayerPlayStylePlus, PlayerPrime, PlayerRole, PlayerRoleAssignment, PlayerSpeciality, PlayerTeam, PlayStyle, PlayStylePlus, Speciality, Stadium, TraitType, FocusType, AccelerationType

class PlayerSerializer(serializers.ModelSerializer):
    # Campo pronto pra usar direto no <img src>: prioriza a versão já
    # baixada/embutida (photo_base64) e cai pro link externo (photo_url)
    # se ainda não tiver sido processada pelo backfill_player_photos.
    photo_data_uri = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = '__all__'

    def get_photo_data_uri(self, obj):
        """
        Prioridade:
          1. Arquivo salvo localmente → retorna URL /media/player_photos/...
          2. Base64 embutido            → retorna data:image/png;base64,...
          3. Link externo (CDN SoFIFA)  → retorna photo_url como fallback
        """
        # 1. Arquivo local (backfill_player_photos já baixou)
        if getattr(obj, "photo", None) and hasattr(obj.photo, "url"):
            return obj.photo.url

        # 2. Base64 armazenado no campo legado
        if getattr(obj, "photo_base64", None):
            return f"data:image/png;base64,{obj.photo_base64}"

        # 3. Link externo como último recurso
        return obj.photo_url or ""

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