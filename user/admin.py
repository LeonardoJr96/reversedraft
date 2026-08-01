from django import forms
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.core.exceptions import ValidationError
from django.shortcuts import render

from .models import User, Watchlist
from .services import grant_credits


class GrantCreditsForm(forms.Form):
    amount = forms.IntegerField(min_value=1, label="Quantidade de créditos a conceder")
    reason = forms.CharField(max_length=200, required=False, label="Motivo (opcional, fica registrado no log)")


@admin.action(description="Conceder créditos de lance aos usuários selecionados")
def conceder_creditos(modeladmin, request, queryset):
    # Ação com página intermediária: o admin escolhe os usuários na listagem,
    # clica na ação, e cai numa tela pedindo a quantidade antes de aplicar.
    if 'apply' in request.POST:
        form = GrantCreditsForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            reason = form.cleaned_data['reason']
            for user in queryset:
                try:
                    grant_credits(user=user, amount=amount, granted_by=request.user, reason=reason)
                except ValidationError as e:
                    modeladmin.message_user(request, f"{user}: {e}", level='error')
            modeladmin.message_user(request, f"{amount} créditos concedidos a {queryset.count()} usuário(s).")
            return None
    else:
        form = GrantCreditsForm()

    return render(request, 'admin/conceder_creditos.html', {
        'users': queryset,
        'form': form,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'title': 'Conceder créditos de lance',
    })


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ['id', 'username', 'email', 'cpf', 'lance_credits', 'is_staff']
    search_fields = ['username', 'email', 'cpf']
    actions = list(DjangoUserAdmin.actions or []) + [conceder_creditos]

    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Dados pessoais', {
            'fields': (
                'cpf',
                'cellphone',
                'address',
                'town',
                'post_code',
                'country',
                'birth_date',
            ),
        }),
    )

    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Dados pessoais', {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'cpf',
                'cellphone',
                'address',
                'town',
                'post_code',
                'country',
                'birth_date',
                'password1',
                'password2',
            ),
        }),
    )


admin.site.register(Watchlist)
