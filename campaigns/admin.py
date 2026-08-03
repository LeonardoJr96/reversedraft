from django.contrib import admin

from .models import Campaign, CampaignAdmin as CampaignAdminMembership, CampaignMembership, MarketWindow, MarketListing, Transfer, MatchPlayerStat
from .services import configure_starting_balance, open_market_window, close_market_window


class CampaignAdminInline(admin.TabularInline):
    model = CampaignAdminMembership
    extra = 0
    autocomplete_fields = ["user"]


class CampaignMembershipInline(admin.TabularInline):
    model = CampaignMembership
    extra = 0
    readonly_fields = ["joined_at"]
    autocomplete_fields = ["user"]


@admin.action(description="Abrir janelas de mercado selecionadas")
def open_windows(modeladmin, request, queryset):
    for window in queryset:
        open_market_window(window)
    modeladmin.message_user(request, f"{queryset.count()} janela(s) aberta(s).")


@admin.action(description="Fechar janelas de mercado selecionadas")
def close_windows(modeladmin, request, queryset):
    for window in queryset:
        close_market_window(window)
    modeladmin.message_user(request, f"{queryset.count()} janela(s) fechada(s).")


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "created_by", "starting_balance", "is_active", "created_at"]
    list_filter = ["is_active", "transfer_policy"]
    search_fields = ["name", "created_by__username"]
    readonly_fields = ["created_at", "created_by"]
    inlines = [CampaignAdminInline, CampaignMembershipInline]


@admin.register(CampaignMembership)
class CampaignMembershipAdmin(admin.ModelAdmin):
    list_display = ["campaign", "user", "starting_balance", "joined_at"]
    list_filter = ["campaign"]
    search_fields = ["campaign__name", "user__username"]
    readonly_fields = ["joined_at"]


@admin.register(CampaignAdminMembership)
class CampaignAdminMembershipAdmin(admin.ModelAdmin):
    list_display = ["campaign", "user"]
    list_filter = ["campaign"]
    search_fields = ["campaign__name", "user__username"]


@admin.register(MarketWindow)
class MarketWindowAdmin(admin.ModelAdmin):
    list_display = ["id", "campaign", "name", "mode", "is_open", "starts_at", "ends_at", "player_count"]
    list_filter = ["is_open", "mode", "campaign"]
    search_fields = ["name", "campaign__name"]
    actions = [open_windows, close_windows]


@admin.register(MarketListing)
class MarketListingAdmin(admin.ModelAdmin):
    list_display = ["id", "campaign_name", "player", "seller", "listing_type", "price", "is_active", "auction"]
    list_filter = ["listing_type", "is_active", "market_window__campaign"]
    search_fields = ["player__common_name", "seller__username"]

    @admin.display(description="Campanha", ordering="market_window__campaign__name")
    def campaign_name(self, obj):
        return obj.market_window.campaign.name


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ["id", "campaign", "requester", "receiver", "status", "created_at"]
    list_filter = ["status", "campaign"]
    search_fields = ["requester__username", "receiver__username"]
    filter_horizontal = ["offered_players", "requested_players"]
    readonly_fields = ["created_at"]


@admin.register(MatchPlayerStat)
class MatchPlayerStatAdmin(admin.ModelAdmin):
    list_display = ["match", "player", "team", "goals", "assists", "created_at"]
    list_filter = ["team"]
    search_fields = ["player__common_name"]
    readonly_fields = ["created_at"]