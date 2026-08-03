from django.contrib import admin

from .models import Competition, CompetitionEntry, Match
from .services import finish_competition


@admin.action(description="Encerrar competições selecionadas")
def finish_selected_competitions(modeladmin, request, queryset):
    finished = 0
    for competition in queryset:
        try:
            finish_competition(competition)
            finished += 1
        except Exception as exc:
            modeladmin.message_user(request, f"{competition}: {exc}", level="ERROR")
    if finished:
        modeladmin.message_user(request, f"{finished} competição(ões) encerrada(s).")


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "competition_type", "campaign", "is_active", "credits_per_win", "credits_per_title", "created_at"]
    list_filter = ["competition_type", "is_active", "campaign"]
    search_fields = ["name"]
    actions = [finish_selected_competitions]


@admin.register(CompetitionEntry)
class CompetitionEntryAdmin(admin.ModelAdmin):
    list_display = ["competition", "team", "points", "created_at"]
    list_filter = ["competition"]
    search_fields = ["competition__name", "team__name"]


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ["id", "competition", "home_team", "away_team", "home_score", "away_score", "status", "round_number", "played_at"]
    list_filter = ["status", "competition"]
    search_fields = ["competition__name", "home_team__name", "away_team__name"]
    readonly_fields = ["played_at"]