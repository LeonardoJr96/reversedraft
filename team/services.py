from django.core.exceptions import ValidationError
from django.db import transaction

from auction.models import Auction
from common.models import Status
from .models import Team, TacticSlot, FormationSlot


def get_roster(user) -> list:
    """Jogadores que o usuário efetivamente ganhou e pagou."""
    auctions = Auction.objects.filter(winner=user, status=Status.PAID).select_related("product__player")
    return [a.product.player for a in auctions if a.product.player_id]


def get_or_create_team(user) -> Team:
    team, _ = Team.objects.get_or_create(owner=user)
    return team


def set_formation(user, formation: str) -> Team:
    valid_formations = set(FormationSlot.objects.values_list("formation", flat=True))
    if formation not in valid_formations:
        raise ValidationError(f"Formação '{formation}' não existe.")

    team = get_or_create_team(user)
    with transaction.atomic():
        team.formation = formation
        team.save()
        # troca de formação limpa os encaixes antigos (slot_codes mudam entre formações)
        TacticSlot.objects.filter(team=team).delete()
    return team


def set_tactic_slot(user, slot_code: str, player_id: int | None) -> TacticSlot:
    team = get_or_create_team(user)

    slot_exists = FormationSlot.objects.filter(formation=team.formation, slot_code=slot_code).exists()
    if not slot_exists:
        raise ValidationError(f"Posição '{slot_code}' não existe na formação {team.formation}.")

    if player_id is not None:
        roster_ids = {p.id for p in get_roster(user)}
        if player_id not in roster_ids:
            raise ValidationError("Você só pode escalar jogadores que ganhou em leilão.")

        # um jogador não pode estar em 2 posições ao mesmo tempo
        TacticSlot.objects.filter(team=team, player_id=player_id).exclude(slot_code=slot_code).delete()

    slot, _ = TacticSlot.objects.update_or_create(
        team=team, slot_code=slot_code, defaults={"player_id": player_id}
    )
    return slot