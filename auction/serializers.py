from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Auction, Bid
from collection.models import UserCard  # ajuste para o app real de collection
from cards.models import Player  # ajuste para o app real dos cards


class PlayerMiniSerializer(serializers.ModelSerializer):
    """Versão enxuta do jogador, só com o necessário pra exibir no card do leilão."""

    class Meta:
        model = Player
        fields = [
            'id', 'fifa_id', 'common_name', 'first_name', 'last_name',
            'overall_rating', 'potential', 'version',
        ]


class UserCardMiniSerializer(serializers.ModelSerializer):
    """Instância da carta + dados do jogador embutidos, pra exibir no leilão."""

    player = PlayerMiniSerializer(read_only=True)

    class Meta:
        model = UserCard
        fields = ['id', 'player', 'source', 'acquired_at']


class BidSerializer(serializers.ModelSerializer):
    bidder_username = serializers.CharField(source='bidder.username', read_only=True)

    class Meta:
        model = Bid
        fields = ['id', 'auction', 'bidder', 'bidder_username', 'amount', 'created_at']
        read_only_fields = ['id', 'created_at', 'bidder_username']

    def validate(self, attrs):
        auction = attrs.get('auction') or getattr(self.instance, 'auction', None)
        amount = attrs.get('amount')

        if not auction.is_active:
            raise serializers.ValidationError(_('Este leilão não está mais ativo.'))

        current_bid = auction.current_bid if auction.current_bid is not None else auction.starting_bid
        if amount <= current_bid:
            raise serializers.ValidationError(
                _('O lance precisa ser maior que o lance atual (%(current)s).') % {'current': current_bid}
            )
        return attrs

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(_('O valor do lance precisa ser maior que zero.'))
        return value


class AuctionSerializer(serializers.ModelSerializer):
    """Serializer de leitura, com detalhes completos do leilão."""

    user_card_detail = UserCardMiniSerializer(source='user_card', read_only=True)
    seller_username = serializers.CharField(source='seller.username', read_only=True)
    highest_bidder_username = serializers.CharField(
        source='highest_bidder.username', read_only=True, default=None
    )
    is_active = serializers.BooleanField(read_only=True)
    bids = BidSerializer(many=True, read_only=True)

    class Meta:
        model = Auction
        fields = [
            'id', 'user_card', 'user_card_detail',
            'seller', 'seller_username',
            'starting_bid', 'current_bid',
            'highest_bidder', 'highest_bidder_username',
            'end_time', 'status', 'is_active',
            'created_at', 'bids',
        ]
        read_only_fields = [
            'id', 'current_bid', 'highest_bidder', 'status', 'is_active',
            'created_at', 'seller_username', 'highest_bidder_username',
            'user_card_detail', 'bids',
        ]


class AuctionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer de escrita, equivalente à view `criar_leilao`.
    `duration_hours` é convertido em `end_time` no create().
    `seller` vem do request, não do payload.

    Valida que o `user_card` pertence a quem está criando o leilão
    e que ele não está travado (já em outro leilão ou escalado num squad).
    """

    duration_hours = serializers.IntegerField(write_only=True, min_value=1)

    class Meta:
        model = Auction
        fields = ['id', 'user_card', 'starting_bid', 'duration_hours']
        read_only_fields = ['id']

    def validate_user_card(self, value):
        request = self.context['request']
        if value.owner_id != request.user.id:
            raise serializers.ValidationError(_('Esta carta não pertence a você.'))
        if value.is_locked:
            raise serializers.ValidationError(
                _('Esta carta já está em uso (leilão ativo ou escalada num squad).')
            )
        return value

    def validate_starting_bid(self, value):
        if value <= 0:
            raise serializers.ValidationError(_('O lance inicial precisa ser maior que zero.'))
        return value

    def create(self, validated_data):
        duration_hours = validated_data.pop('duration_hours')
        validated_data['seller'] = self.context['request'].user
        validated_data['end_time'] = timezone.now() + timezone.timedelta(hours=duration_hours)

        user_card = validated_data['user_card']
        auction = Auction.objects.create(**validated_data)

        # Trava a carta assim que o leilão é criado, pra não poder
        # ser usada em squad nem leiloada de novo enquanto pendente.
        user_card.is_locked = True
        user_card.save(update_fields=['is_locked'])

        return auction