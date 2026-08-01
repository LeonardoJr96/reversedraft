import base64
import binascii
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.db import transaction

from .models import Player, AccelerationType


def _decode_photo(photo_base64: str | None, sofifa_id) -> ContentFile | None:
    """Decodifica a foto em base64 mandada pelo scraper.
    Retorna None (sem quebrar o import) se o campo não vier ou vier corrompido —
    o jogador é salvo normalmente, só sem foto nessa rodada."""
    if not photo_base64:
        return None
    try:
        raw = base64.b64decode(photo_base64, validate=True)
    except (binascii.Error, ValueError):
        return None
    return ContentFile(raw, name=f"{sofifa_id}.png")


def fetch_photo_as_file(photo_url: str | None, sofifa_id: int | str | None = None) -> ContentFile | None:
    """Baixa uma foto a partir de uma URL e retorna um ContentFile pronto para salvar."""
    if not photo_url:
        return None

    try:
        request = Request(photo_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=10) as response:
            raw = response.read()
    except (HTTPError, URLError, TimeoutError, ValueError):
        return None

    if not raw:
        return None

    filename = f"{sofifa_id or 'player'}.png"
    return ContentFile(raw, name=filename)


def fetch_photo_as_base64(photo_url: str | None, sofifa_id: int | str | None = None) -> str | None:
    """Compatibilidade com comandos antigos que esperam uma string em base64."""
    photo_file = fetch_photo_as_file(photo_url, sofifa_id)
    if photo_file is None:
        return None

    return base64.b64encode(photo_file.read()).decode("ascii")


def upsert_player(data: dict) -> Player:
    accel = None
    if data.get("acceleration_type"):
        accel, _ = AccelerationType.objects.get_or_create(name=data["acceleration_type"])

    defaults = {
        "positions": data.get("positions", []),
        "best_position": data.get("best_position"),
        "international_reputation": data.get("international_reputation"),
        "playstyles": data.get("playstyles", []),
        "player_roles": data.get("roles", []),
        "common_name": data["name"],
        "age": data.get("age"),
        "height": data.get("height"),
        "weight": data.get("weight"),
        "foot": data.get("foot"),
        "skill_moves": data.get("skill_moves"),
        "weak_foot": data.get("weak_foot"),
        "acceleration_type": accel,
        "photo_url": data.get("photo_url"),
        "price": int(data["value"]) if data.get("value") else None,
        "wage": int(data["wage"]) if data.get("wage") else None,
        "overall_rating": data.get("overallrating"),
        "potential": data.get("potential"),
        "pac": data.get("pac"), "sho": data.get("sho"), "pas": data.get("pas"),
        "dri": data.get("dri"), "def_rating": data.get("def_rating"), "phy": data.get("phy"),
        "crossing": data.get("crossing"),
        "finishing": data.get("finishing"),
        "heading": data.get("headingaccuracy"),
        "short_passing": data.get("shortpassing"),
        "volleys": data.get("volleys"),
        "dribbling": data.get("dribbling"),
        "curve": data.get("curve"),
        "free_kick": data.get("fk_accuracy"),
        "long_passing": data.get("longpassing"),
        "ball_control": data.get("ballcontrol"),
        "acceleration": data.get("acceleration"),
        "sprint_speed": data.get("sprintspeed"),
        "agility": data.get("agility"),
        "reactions": data.get("reactions"),
        "balance": data.get("balance"),
        "shot_power": data.get("shotpower"),
        "jumping": data.get("jumping"),
        "stamina": data.get("stamina"),
        "strength": data.get("strength"),
        "long_shots": data.get("longshots"),
        "aggression": data.get("aggression"),
        "interceptions": data.get("interceptions"),
        "positioning": data.get("positioning"),
        "vision": data.get("vision"),
        "penalties": data.get("penalties"),
        "composure": data.get("composure"),
        "marking": data.get("defensiveawareness"),
        "standing_tackle": data.get("standingtackle"),
        "sliding_tackle": data.get("slidingtackle"),
        "gk_diving": data.get("gk_diving"),
        "gk_handling": data.get("gk_handling"),
        "gk_kicking": data.get("gk_kicking"),
        "gk_positioning": data.get("gk_positioning"),
        "gk_reflexes": data.get("gk_reflexes"),
    }

    photo_file = _decode_photo(data.get("photo_base64"), data["sofifa_id"])
    if photo_file is not None:
        defaults["photo"] = photo_file

    player, _created = Player.objects.update_or_create(
        fifa_id=data["sofifa_id"], defaults=defaults
    )
    return player


def import_players_bulk(rows: list[dict]) -> list[Player]:
    with transaction.atomic():
        return [upsert_player(row) for row in rows]