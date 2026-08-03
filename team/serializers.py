from rest_framework import serializers
from fifa_data.serializers import PlayerSerializer
from .models import Team, TacticSlot, FormationSlot


class FormationSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormationSlot
        fields = ["slot_code", "label", "x", "y", "order"]


class TacticSlotSerializer(serializers.ModelSerializer):
    player = PlayerSerializer(read_only=True)

    class Meta:
        model = TacticSlot
        fields = ["slot_code", "player"]


class TeamSerializer(serializers.ModelSerializer):
    slots = TacticSlotSerializer(many=True, read_only=True)
    formation_layout = serializers.SerializerMethodField()
    balance = serializers.DecimalField(source='owner.balance', max_digits=12, decimal_places=2, read_only=True)
    player_count = serializers.IntegerField(source='roster_entries.count', read_only=True)

    class Meta:
        model = Team
        fields = ["id", "name", "formation", "balance", "player_count", "slots", "formation_layout", "updated_at"]

    def get_formation_layout(self, obj):
        layout = FormationSlot.objects.filter(formation=obj.formation)
        return FormationSlotSerializer(layout, many=True).data
