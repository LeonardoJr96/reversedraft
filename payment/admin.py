from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "type", "status", "amount", "balance_after", "auction", "created_at"]
    list_filter = ["type", "status"]
    search_fields = ["user__username", "notes"]
    readonly_fields = ["user", "auction", "type", "status", "amount", "balance_after", "notes", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False