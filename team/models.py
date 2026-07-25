from django.db import models


FORMATION_CHOICES = [
    ("4-3-3", "4-3-3"),
    ("4-4-2", "4-4-2"),
    ("3-5-2", "3-5-2"),
    ("4-2-3-1", "4-2-3-1"),
]


class FormationSlot(models.Model):
    """
    Define as posições fixas de cada formação, com coordenada em % pra
    desenhar o campinho no front (x=0 esquerda, x=100 direita, y=0 fundo
    da defesa, y=100 ataque).
    """
    formation = models.CharField(max_length=10, choices=FORMATION_CHOICES)
    slot_code = models.CharField(max_length=10)   # 'GK', 'LB', 'CB1', 'CM1'...
    label = models.CharField(max_length=20)        # 'Goleiro', 'Zagueiro'...
    x = models.FloatField()
    y = models.FloatField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("formation", "slot_code")
        ordering = ["formation", "order"]


class Team(models.Model):
    owner = models.OneToOneField("user.User", on_delete=models.CASCADE, related_name="team")
    name = models.CharField(max_length=100, blank=True)
    formation = models.CharField(max_length=10, choices=FORMATION_CHOICES, default="4-3-3")
    updated_at = models.DateTimeField(auto_now=True)


class TacticSlot(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="slots")
    slot_code = models.CharField(max_length=10)
    player = models.ForeignKey(
        "fifa_data.Player", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        unique_together = ("team", "slot_code")