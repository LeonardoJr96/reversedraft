from django.contrib import admin
from .models import Team, TacticSlot, FormationSlot

class TacticSlotInline(admin.TabularInline):
    model = TacticSlot
    extra = 0

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["id", "owner", "formation", "updated_at"]
    inlines = [TacticSlotInline]

@admin.register(FormationSlot)
class FormationSlotAdmin(admin.ModelAdmin):
    list_display = ["formation", "slot_code", "label", "x", "y", "order"]
    list_filter = ["formation"]