# user/services.py
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import User
from common.services import log_personal_data_access


def register_user(data):
    """
    Cria um novo usuário com os dados fornecidos.
    """
    user = User.objects.create_user(
        **data
    )

    return user


def grant_credits(*, user, amount, granted_by, reason=""):
    """
    Concede créditos de lance diretamente ao usuário, sem passar pelo
    fluxo de pagamento. Uso típico: suporte ao cliente, cortesia,
    ou destravar testes/homologação enquanto o gateway de pagamento
    real ainda não está integrado.

    Segue o mesmo padrão de `auction.services.place_bid`: tranca a
    linha do usuário (select_for_update) para evitar condição de corrida
    se dois administradores concederem crédito ao mesmo usuário ao
    mesmo tempo.
    """
    if amount <= 0:
        raise ValidationError("A quantidade de créditos concedidos deve ser positiva.")

    with transaction.atomic():
        locked_user = User.objects.select_for_update().get(pk=user.pk)
        locked_user.lance_credits += amount
        locked_user.save()

    log_personal_data_access(
        actor=granted_by,
        subject=user,
        action=f"creditos_concedidos_manualmente:{amount}:{reason}".strip(':'),
    )

    return locked_user
