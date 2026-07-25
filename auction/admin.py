# auction/admin.py
from django.contrib import admin
from django.utils import timezone
from django.core.exceptions import ValidationError


from .models import Auction, Bid

from .services import close_auction, reopen_auction


@admin.action(description="Fechar leilão selecionado e apurar vencedor")
def fechar_leiloes(modeladmin, request, queryset):
    for auction in queryset:
        close_auction(auction)

@admin.action(description="Reabrir leilão para novos lances (leilão expirado)")
def reabrir_leiloes(modeladmin, request, queryset):
    for auction in queryset:
        try:
            novo = reopen_auction(auction)
            modeladmin.message_user(request, f"Leilão {auction.id} reaberto como novo leilão #{novo.id}.")
        except ValidationError as e:
            modeladmin.message_user(request, f"Leilão {auction.id}: {e}", level='error')

@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'status', 'winner', 'number_of_bids', 'time_ending']
    list_filter = ['status']
    readonly_fields = ['number_of_bids', 'winner', 'status', 'payment_deadline']
    actions = [fechar_leiloes, reabrir_leiloes]


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ['id', 'auction', 'user', 'price', 'bid_time']
    list_filter = ['auction']
    search_fields = ['user__username', 'user__cpf']