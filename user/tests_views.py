from decimal import Decimal
from datetime import timedelta, date

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APIClient

from products.models import Product
from auction.models import Auction
from auction.services import place_bid

from .models import User
from .services import grant_credits


def make_user(**overrides):
    username = overrides.get('username', 'user')
    defaults = dict(
        password='SenhaForte123!', email=f'{username}@example.com',
        cellphone='49999999999', address='Rua X', town='Joinville',
        post_code='89200000', country='Brasil', birth_date='1990-01-01',
    )
    defaults.update(overrides)
    return User.objects.create_user(**defaults)


class RegisterViewTests(TestCase):
    """Cadastro público — Cláusula 15.1-a: exige 18 anos ou mais."""

    def setUp(self):
        self.client = APIClient()
        self.payload = {
            'username': 'novoUsuario',
            'password': 'SenhaForte123!',
            'password_confirm': 'SenhaForte123!',
            'email': 'novo@example.com',
            'cpf': '12345678900',
            'cellphone': '49988715872',
            'address': 'Rua Santa Catarina, 864',
            'town': "Herval d'Oeste",
            'post_code': '89610-000',
            'country': 'Brasil',
            'first_name': 'Novo',
            'last_name': 'Usuário',
            'accept_terms': True,
        }

    def test_cadastro_com_maior_de_idade_e_aceito(self):
        self.payload['birth_date'] = '1995-04-20'
        response = self.client.post('/api/v1/users/register/', self.payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['lance_credits'], 0)

    def test_cadastro_de_menor_de_idade_e_recusado(self):
        hoje = date.today()
        nascimento_menor = hoje.replace(year=hoje.year - 17)
        self.payload['birth_date'] = nascimento_menor.isoformat()
        response = self.client.post('/api/v1/users/register/', self.payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('birth_date', response.data)

    def test_cadastro_sem_aceitar_termos_e_recusado(self):
        self.payload['birth_date'] = '1995-04-20'
        self.payload['accept_terms'] = False
        response = self.client.post('/api/v1/users/register/', self.payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_senhas_diferentes_sao_recusadas(self):
        self.payload['birth_date'] = '1995-04-20'
        self.payload['password_confirm'] = 'OutraSenha1!'
        response = self.client.post('/api/v1/users/register/', self.payload, format='json')
        self.assertEqual(response.status_code, 400)


class MeViewTests(TestCase):
    """'Minha conta' — Cláusula 2.1.1: saldo de lances e histórico de participações."""

    def setUp(self):
        self.user = make_user(username='camila_conta', cpf='77788899900', lance_credits=5)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_me_retorna_saldo_e_dados_do_perfil(self):
        response = self.client.get('/api/v1/users/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['lance_credits'], 5)
        self.assertEqual(response.data['username'], 'camila_conta')

    def test_get_me_retorna_historico_de_lances_com_status(self):
        product = Product.objects.create(title='Relógio', description='d', quantity=1, category='c', price=1000)
        auction = Auction.objects.create(
            product=product, time_starting=timezone.now(), time_ending=timezone.now() + timedelta(days=1),
        )
        place_bid(self.user, auction, Decimal('37.42'))

        response = self.client.get('/api/v1/users/me/')

        self.assertEqual(len(response.data['bid_history']), 1)
        item = response.data['bid_history'][0]
        self.assertEqual(item['product_title'], 'Relógio')
        self.assertEqual(item['status'], 'em_andamento')

    def test_patch_me_edita_campos_permitidos(self):
        response = self.client.patch('/api/v1/users/me/', {'address': 'Novo Endereço, 999'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.address, 'Novo Endereço, 999')

    def test_patch_me_nao_permite_alterar_cpf(self):
        cpf_original = self.user.cpf
        response = self.client.patch('/api/v1/users/me/', {'cpf': '00000000000'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.cpf, cpf_original)  # campo somente-leitura, ignorado silenciosamente

    def test_usuario_nao_autenticado_nao_acessa_me(self):
        client_anonimo = APIClient()
        response = client_anonimo.get('/api/v1/users/me/')
        self.assertEqual(response.status_code, 401)


class ChangePasswordViewTests(TestCase):
    def setUp(self):
        self.user = make_user(username='trocar_senha', cpf='11100022233')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_troca_senha_com_senha_atual_correta(self):
        response = self.client.post('/api/v1/users/change-password/', {
            'current_password': 'SenhaForte123!',
            'new_password': 'NovaSenha1!',
            'new_password_confirm': 'NovaSenha1!',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NovaSenha1!'))

    def test_troca_senha_com_senha_atual_errada_e_recusada(self):
        response = self.client.post('/api/v1/users/change-password/', {
            'current_password': 'SenhaErrada',
            'new_password': 'NovaSenha1!',
            'new_password_confirm': 'NovaSenha1!',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('SenhaForte123!'))  # não mudou

    def test_nova_senha_fraca_e_recusada(self):
        response = self.client.post('/api/v1/users/change-password/', {
            'current_password': 'SenhaForte123!',
            'new_password': '123',
            'new_password_confirm': '123',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_nova_senha_e_confirmacao_diferentes_sao_recusadas(self):
        response = self.client.post('/api/v1/users/change-password/', {
            'current_password': 'SenhaForte123!',
            'new_password': 'NovaSenha1!',
            'new_password_confirm': 'OutraCoisa1!',
        }, format='json')
        self.assertEqual(response.status_code, 400)


class GrantCreditsTests(TestCase):
    """Concessão manual de créditos pelo admin, sem depender de pagamento."""

    def setUp(self):
        self.admin = make_user(username='admin_teste', cpf='00000000001', is_staff=True)
        self.user = make_user(username='beneficiario', cpf='00000000002', lance_credits=3)

    def test_concede_creditos_e_soma_ao_saldo_existente(self):
        grant_credits(user=self.user, amount=10, granted_by=self.admin, reason='teste')
        self.user.refresh_from_db()
        self.assertEqual(self.user.lance_credits, 13)

    def test_quantidade_zero_ou_negativa_e_recusada(self):
        with self.assertRaises(ValidationError):
            grant_credits(user=self.user, amount=0, granted_by=self.admin)
        with self.assertRaises(ValidationError):
            grant_credits(user=self.user, amount=-5, granted_by=self.admin)
