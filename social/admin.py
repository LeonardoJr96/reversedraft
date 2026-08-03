from django.contrib import admin

from .models import Conversation, Friendship, Message


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ["requester", "addressee", "status", "created_at", "responded_at"]
    list_filter = ["status"]
    search_fields = ["requester__username", "addressee__username"]
    readonly_fields = ["created_at", "responded_at"]


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "type", "campaign", "created_at"]
    list_filter = ["type"]
    search_fields = ["campaign__name"]
    filter_horizontal = ["participants"]
    readonly_fields = ["created_at"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation", "sender", "text_preview", "created_at"]
    list_filter = ["conversation"]
    search_fields = ["sender__username", "text"]
    readonly_fields = ["created_at"]

    @admin.display(description="Mensagem")
    def text_preview(self, obj):
        return obj.text[:80]