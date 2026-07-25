from django.core.management.base import BaseCommand
from team.models import FormationSlot

FORMATIONS = {
    "4-3-3": [
        ("GK", "Goleiro", 50, 5),
        ("LB", "Lateral Esq.", 15, 25), ("CB1", "Zagueiro", 35, 20),
        ("CB2", "Zagueiro", 65, 20), ("RB", "Lateral Dir.", 85, 25),
        ("CM1", "Meio", 30, 50), ("CM2", "Meio", 50, 45), ("CM3", "Meio", 70, 50),
        ("LW", "Ponta Esq.", 20, 80), ("ST", "Atacante", 50, 85), ("RW", "Ponta Dir.", 80, 80),
    ],
    "4-4-2": [
        ("GK", "Goleiro", 50, 5),
        ("LB", "Lateral Esq.", 15, 25), ("CB1", "Zagueiro", 35, 20),
        ("CB2", "Zagueiro", 65, 20), ("RB", "Lateral Dir.", 85, 25),
        ("LM", "Meia Esq.", 15, 55), ("CM1", "Meio", 40, 50),
        ("CM2", "Meio", 60, 50), ("RM", "Meia Dir.", 85, 55),
        ("ST1", "Atacante", 40, 85), ("ST2", "Atacante", 60, 85),
    ],
    # 3-5-2 e 4-2-3-1: mesmo padrão, adiciona quando quiser
}

class Command(BaseCommand):
    help = "Popula as posições fixas de cada formação"

    def handle(self, *args, **options):
        FormationSlot.objects.all().delete()
        for formation, slots in FORMATIONS.items():
            for i, (code, label, x, y) in enumerate(slots):
                FormationSlot.objects.create(
                    formation=formation, slot_code=code, label=label, x=x, y=y, order=i
                )
        self.stdout.write(self.style.SUCCESS("Formações populadas."))