from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from fifa_data.serializers import PlayerSerializer
from .services import create_custom_formation, delete_custom_formation, get_or_create_team, get_roster, set_formation, set_tactic_slot, update_custom_formation
from .serializers import FormationSlotSerializer, TeamSerializer


class MyTeamView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        campaign_id = request.query_params.get('campaign_id')
        campaign = None
        if campaign_id:
            from campaigns.models import Campaign
            campaign = Campaign.objects.filter(pk=campaign_id).first()
        team = get_or_create_team(request.user, campaign)
        return Response(TeamSerializer(team).data)

    def patch(self, request):
        """Body: {"formation": "4-4-2", "campaign_id": 1} ou {"formation": "Minha 1-2-3", "slots": [...], "campaign_id": 1}"""
        formation = request.data.get("formation")
        campaign_id = request.data.get("campaign_id")
        campaign = None
        if campaign_id:
            from campaigns.models import Campaign
            campaign = Campaign.objects.filter(pk=campaign_id).first()
        try:
            if request.data.get("slots") and formation:
                create_custom_formation(request.user, formation, request.data.get("slots"), campaign)
            team = set_formation(request.user, formation, campaign)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)
        return Response(TeamSerializer(team).data)


class MyRosterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        roster = get_roster(request.user)
        return Response(PlayerSerializer(roster, many=True).data)


class MyFormationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import FormationSlot
        formations = FormationSlot.objects.values('formation').distinct().order_by('formation')
        return Response(list(formations))

    def post(self, request):
        formation_name = request.data.get('formation')
        slots = request.data.get('slots', [])
        if not formation_name:
            return Response({'detail': 'formation is required'}, status=400)

        try:
            if request.data.get('update', False):
                update_custom_formation(request.user, formation_name, slots)
            else:
                create_custom_formation(request.user, formation_name, slots)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=400)

        from .models import FormationSlot
        layout = FormationSlot.objects.filter(formation=formation_name).order_by('order', 'id')
        return Response(FormationSlotSerializer(layout, many=True).data)

    def delete(self, request):
        formation_name = request.query_params.get('formation')
        if not formation_name:
            return Response({'detail': 'formation is required'}, status=400)

        try:
            delete_custom_formation(request.user, formation_name)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=400)

        return Response({'detail': 'formation deleted'})


class TacticSlotView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, slot_code):
        """Body: {"player_id": 123, "campaign_id": 1}  (ou {"player_id": null} pra esvaziar a posição)"""
        campaign_id = request.data.get("campaign_id")
        campaign = None
        if campaign_id:
            from campaigns.models import Campaign
            campaign = Campaign.objects.filter(pk=campaign_id).first()
        try:
            slot = set_tactic_slot(request.user, slot_code, request.data.get("player_id"), campaign)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)
        from .serializers import TacticSlotSerializer
        return Response(TacticSlotSerializer(slot).data)