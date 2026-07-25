from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import User

from common.validators import validate_confirm_password, validate_strong_password

class UserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    accept_terms = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        fields = '__all__'
        read_only_fields = ['last_login', 'is_superuser','lance_credits', 'is_staff','is_active','date_joined', 'groups', 'user_permissions', 'terms_accepted_at','self_excluded_until',]

    def validate_accept_terms(self, value):
        if not value:
            raise serializers.ValidationError(
                "É necessário aceitar os Termos de Uso e a Política de Privacidade."
            )
        return value

    def validate_password(self, value):
        """
        Valida a senha usando os validadores configurados em AUTH_PASSWORD_VALIDATORS.
        """
        try:
            username = self.initial_data.get('username')
            email = self.initial_data.get('email')
            validate_strong_password(value, username=username, email=email)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate(self, data):
        if not validate_confirm_password(data['password'], data['password_confirm']):
            raise serializers.ValidationError(
                {'password_confirm': 'As senhas não coincidem.'}
            )
        return data


class MyBidSerializer(serializers.Serializer):
    """
    Um item do histórico de participações de 'minha conta'.
    Não é ModelSerializer porque mistura dado do Bid com o status
    calculado (que já existe pronto em auction.services.get_bid_status)
    e o título do produto do leilão — é uma "view" combinada, não um
    espelho 1:1 de uma tabela.
    """
    id = serializers.IntegerField()
    auction = serializers.IntegerField(source='auction_id')
    product_title = serializers.CharField(source='auction.product.title')
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    bid_time = serializers.DateTimeField()
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        from auction.services import get_bid_status
        return get_bid_status(obj)


class MeSerializer(serializers.ModelSerializer):
    """
    Serializer de 'minha conta' (Cláusula 2.1.1: "Área minha conta, com
    saldo de lances e histórico de participações"). Campos de identidade
    (username, email, cpf, birth_date) ficam somente leitura de propósito:
    trocar e-mail/CPF tem implicação de segurança e legal que merece um
    fluxo próprio (com confirmação), não uma edição solta de perfil.
    """
    bid_history = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'cpf', 'birth_date',
            'cellphone', 'address', 'town', 'post_code', 'country',
            'lance_credits', 'bid_history',
        ]
        read_only_fields = ['id', 'username', 'email', 'cpf', 'birth_date', 'lance_credits', 'bid_history']

    def get_bid_history(self, obj):
        # Import local (não no topo do arquivo) de propósito: user/serializers.py
        # não deveria ter uma dependência estrutural de auction, só a view de
        # "minha conta" (que é uma camada de agregação, não o núcleo do domínio
        # de usuário) precisa conhecer Bid. É a mesma lição da Correção 1: manter
        # o acoplamento o mais localizado possível.
        from auction.models import Bid
        bids = Bid.objects.filter(user=obj).select_related('auction', 'auction__product').order_by('-bid_time')
        return MyBidSerializer(bids, many=True).data


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        user = self.context['request'].user
        try:
            validate_strong_password(value, username=user.username, email=user.email)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, data):
        if not validate_confirm_password(data['new_password'], data['new_password_confirm']):
            raise serializers.ValidationError({'new_password_confirm': 'As senhas não coincidem.'})
        return data