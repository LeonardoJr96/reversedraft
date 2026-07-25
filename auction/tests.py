from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

from user.models import User
from products.models import Product
from .models import Auction, Bid
from .services import place_bid, get_winning_bid, close_auction
from common.models import Status


class PlaceBidTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='camila', password='SenhaForte123!', email='camila@example.com',
            cpf='12345678900', cellphone='49999999999', address='Rua X',
            town='Joinville', post_code='89200000', country='Brasil',
            birth_date='1990-01-01', lance_credits=5,
        )
        self.product = Product.objects.create(
            title='Relógio', description='Relógio de luxo', quantity=1,
            category='Acessórios', price=1000,
        )
        self.auction = Auction.objects.create(
            product=self.product,
            time_starting=timezone.now(),
            time_ending=timezone.now() + timedelta(days=1),
        )

    def test_bid_desconta_credito(self):
        place_bid(self.user, self.auction, 10)
        self.user.refresh_from_db()
        self.assertEqual(self.user.lance_credits, 4)

    def test_bid_repetido_pelo_mesmo_usuario_e_recusado(self):
        place_bid(self.user, self.auction, 10)
        with self.assertRaises(ValidationError):
            place_bid(self.user, self.auction, 10)

    def test_bid_repetido_nao_desconta_credito_na_falha(self):
        place_bid(self.user, self.auction, 10)
        try:
            place_bid(self.user, self.auction, 10)
        except ValidationError:
            pass
        self.user.refresh_from_db()
        self.assertEqual(self.user.lance_credits, 4)  # só descontou 1 vez

    def test_sem_credito_nao_deixa_apostar(self):
        self.user.lance_credits = 0
        self.user.save()
        with self.assertRaises(ValidationError):
            place_bid(self.user, self.auction, 10)


class GetWinningBidTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            title='Relógio', description='Relógio', quantity=1,
            category='Acessórios', price=1000,
        )
        self.auction = Auction.objects.create(
            product=self.product,
            time_starting=timezone.now(),
            time_ending=timezone.now() + timedelta(days=1),
        )
        self.u1 = User.objects.create_user(
            username='u1', password='SenhaForte123!', email='u1@example.com',
            cpf='11111111111', cellphone='49111111111', address='A',
            town='Joinville', post_code='89200000', country='Brasil',
            birth_date='1990-01-01', lance_credits=5,
        )
        self.u2 = User.objects.create_user(
            username='u2', password='SenhaForte123!', email='u2@example.com',
            cpf='22222222222', cellphone='49222222222', address='B',
            town='Joinville', post_code='89200000', country='Brasil',
            birth_date='1990-01-01', lance_credits=5,
        )

    def test_empate_no_menor_valor_passa_pro_proximo_unico(self):
        Bid.objects.create(user=self.u1, auction=self.auction, price=5, bid_time=timezone.now())
        Bid.objects.create(user=self.u2, auction=self.auction, price=5, bid_time=timezone.now())
        Bid.objects.create(user=self.u1, auction=self.auction, price=8, bid_time=timezone.now())

        vencedor = get_winning_bid(self.auction)
        self.assertEqual(vencedor.price, 8)

    def test_fecha_leilao_sem_vencedor_unico(self):
        Bid.objects.create(user=self.u1, auction=self.auction, price=5, bid_time=timezone.now())
        Bid.objects.create(user=self.u2, auction=self.auction, price=5, bid_time=timezone.now())

        close_auction(self.auction)
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.status, Status.NO_WINNER)