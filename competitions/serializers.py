from rest_framework import serializers

from .models import Competition, Match


class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = '__all__'


class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = '__all__'


class BracketMatchSerializer(MatchSerializer):
    home_team = serializers.PrimaryKeyRelatedField(read_only=True)
    away_team = serializers.PrimaryKeyRelatedField(read_only=True)
    next_match = serializers.PrimaryKeyRelatedField(read_only=True)
