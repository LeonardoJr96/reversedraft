from django.core.exceptions import ValidationError
from django.db import transaction

from auction.models import Auction
from common.models import Status
from .models import Team, TacticSlot, FormationSlot


def create_custom_formation(user, formation_name: str, slots: list[dict], campaign=None) -> str:
    """Cria uma formação customizada para o usuário e retorna o nome dela."""
    if not formation_name or not formation_name.strip():
        raise ValidationError('O nome da formação é obrigatório.')

    if FormationSlot.objects.filter(formation=formation_name).exists():
        raise ValidationError('Essa formação já existe.')

    if not slots:
        raise ValidationError('É necessário informar pelo menos um slot.')

    with transaction.atomic():
        for idx, slot in enumerate(slots):
            slot_code = slot.get('slot_code')
            label = slot.get('label')
            if not slot_code or not label:
                raise ValidationError('Cada slot precisa de slot_code e label.')
            FormationSlot.objects.create(
                formation=formation_name,
                slot_code=slot_code,
                label=label,
                x=slot.get('x', 0),
                y=slot.get('y', 0),
                order=slot.get('order', idx),
            )

    return formation_name


def update_custom_formation(user, formation_name: str, slots: list[dict], campaign=None) -> str:
    """Atualiza uma formação customizada existente, substituindo seus slots."""
    if not formation_name or not formation_name.strip():
        raise ValidationError('O nome da formação é obrigatório.')

    if not slots:
        raise ValidationError('É necessário informar pelo menos um slot.')

    with transaction.atomic():
        FormationSlot.objects.filter(formation=formation_name).delete()
        for idx, slot in enumerate(slots):
            slot_code = slot.get('slot_code')
            label = slot.get('label')
            if not slot_code or not label:
                raise ValidationError('Cada slot precisa de slot_code e label.')
            FormationSlot.objects.create(
                formation=formation_name,
                slot_code=slot_code,
                label=label,
                x=slot.get('x', 0),
                y=slot.get('y', 0),
                order=slot.get('order', idx),
            )

    return formation_name


def delete_custom_formation(user, formation_name: str, campaign=None) -> None:
    """Remove uma formação customizada e seus slots."""
    if not formation_name or not formation_name.strip():
        raise ValidationError('O nome da formação é obrigatório.')

    FormationSlot.objects.filter(formation=formation_name).delete()


def get_or_create_team(user, campaign=None) -> Team:
    team, _ = Team.objects.get_or_create(owner=user, campaign=campaign)
    return team


def get_roster(user, campaign=None) -> list:
    """Retorna os jogadores presentes no `RosterEntry` do time do usuário.

    Se `campaign` for fornecida, retorna o elenco daquele time na campanha;
    caso contrário, retorna o time global (campaign=None).
    """
    team = get_or_create_team(user, campaign)
    entries = team.roster_entries.select_related('player').all()
    return [e.player for e in entries]


def set_formation(user, formation: str, campaign=None) -> Team:
    valid_formations = set(FormationSlot.objects.values_list("formation", flat=True))
    if formation not in valid_formations:
        raise ValidationError(f"Formação '{formation}' não existe.")

    team = get_or_create_team(user, campaign)
    with transaction.atomic():
        team.formation = formation
        team.save()
        # troca de formação limpa os encaixes antigos (slot_codes mudam entre formações)
        TacticSlot.objects.filter(team=team).delete()
    return team


def set_tactic_slot(user, slot_code: str, player_id: int | None, campaign=None) -> TacticSlot:
    team = get_or_create_team(user, campaign)

    slot_exists = FormationSlot.objects.filter(formation=team.formation, slot_code=slot_code).exists()
    if not slot_exists:
        raise ValidationError(f"Posição '{slot_code}' não existe na formação {team.formation}.")

    if player_id is not None:
        roster_ids = {p.id for p in get_roster(user, campaign)}
        if player_id not in roster_ids:
            raise ValidationError("Você só pode escalar jogadores que ganhou em leilão.")

        # um jogador não pode estar em 2 posições ao mesmo tempo
        TacticSlot.objects.filter(team=team, player_id=player_id).exclude(slot_code=slot_code).delete()

    slot, _ = TacticSlot.objects.update_or_create(
        team=team, slot_code=slot_code, defaults={"player_id": player_id}
    )
    return slot