"""
Baixa a foto de cada jogador (Player.photo_url, CDN do sofifa) e salva em
Player.photo_base64, para o front consumir a imagem já embutida (data URI)
em vez de depender de hotlink direto no CDN externo.

Uso:
    python manage.py backfill_player_photos
    python manage.py backfill_player_photos --limit 500
    python manage.py backfill_player_photos --force   # rebaixa mesmo quem já tem
"""

from django.core.management.base import BaseCommand
from django.db.models import Q

from fifa_data.models import Player
from fifa_data.services import fetch_photo_as_base64


class Command(BaseCommand):
    help = "Baixa fotos dos jogadores (photo_url) e preenche photo_base64."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None, help="Limitar quantidade de jogadores processados")
        parser.add_argument("--force", action="store_true", help="Rebaixar mesmo quem já tem photo_base64")

    def handle(self, *args, **options):
        qs = Player.objects.exclude(Q(photo_url__isnull=True) | Q(photo_url__exact=""))

        if not options["force"]:
            qs = qs.filter(Q(photo_base64__isnull=True) | Q(photo_base64__exact=""))

        if options["limit"]:
            qs = qs[: options["limit"]]

        total = qs.count()
        self.stdout.write(f"Processando {total} jogador(es)...")

        ok = fail = 0
        for i, player in enumerate(qs.iterator(), start=1):
            encoded = fetch_photo_as_base64(player.photo_url)
            if encoded:
                player.photo_base64 = encoded
                player.save(update_fields=["photo_base64"])
                ok += 1
            else:
                fail += 1

            if i % 100 == 0:
                self.stdout.write(f"  {i}/{total} (ok={ok}, falhas={fail})")

        self.stdout.write(self.style.SUCCESS(f"Concluído: {ok} ok, {fail} falha(s)."))