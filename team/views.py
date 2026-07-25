from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from fifa_data.serializers import PlayerSerializer
from .services import get_or_create_team, get_roster, set_formation, set_tactic_slot
from .serializers import TeamSerializer


class MyTeamView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        team = get_or_create_team(request.user)
        return Response(TeamSerializer(team).data)

    def patch(self, request):
        """Body: {"formation": "4-4-2"}"""
        formation = request.data.get("formation")
        try:
            team = set_formation(request.user, formation)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)
        return Response(TeamSerializer(team).data)


class MyRosterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        roster = get_roster(request.user)
        return Response(PlayerSerializer(roster, many=True).data)


class TacticSlotView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, slot_code):
        """Body: {"player_id": 123}  (ou {"player_id": null} pra esvaziar a posição)"""
        try:
            slot = set_tactic_slot(request.user, slot_code, request.data.get("player_id"))
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)
        from .serializers import TacticSlotSerializer
        return Response(TacticSlotSerializer(slot).data)