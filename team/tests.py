from django.test import TestCase

from user.models import User
from team.models import FormationSlot
from team.services import create_custom_formation, delete_custom_formation, get_or_create_team, set_formation, update_custom_formation


class TeamFormationTests(TestCase):
    def test_create_custom_formation_and_use_it(self):
        user = User.objects.create_user(
            username='coach', email='coach@example.com', password='x', cpf='999',
            cellphone='', address='', town='', post_code='', country='', birth_date='1990-01-01'
        )

        slots = [
            {'slot_code': 'GK', 'label': 'Goleiro', 'x': 50, 'y': 5, 'order': 0},
            {'slot_code': 'CB', 'label': 'Zagueiro', 'x': 35, 'y': 20, 'order': 1},
            {'slot_code': 'ST', 'label': 'Atacante', 'x': 65, 'y': 80, 'order': 2},
        ]

        formation_name = create_custom_formation(user, 'Minha 1-2-3', slots)

        self.assertTrue(FormationSlot.objects.filter(formation=formation_name).exists())

        team = set_formation(user, formation_name)
        self.assertEqual(team.formation, formation_name)
        self.assertTrue(FormationSlot.objects.filter(formation=formation_name).count() >= 3)

    def test_update_and_delete_custom_formation(self):
        user = User.objects.create_user(
            username='coach2', email='coach2@example.com', password='x', cpf='998',
            cellphone='', address='', town='', post_code='', country='', birth_date='1990-01-01'
        )

        create_custom_formation(user, 'Minha 3-4-3', [
            {'slot_code': 'GK', 'label': 'Goleiro', 'x': 50, 'y': 5, 'order': 0},
            {'slot_code': 'CB', 'label': 'Zagueiro', 'x': 35, 'y': 20, 'order': 1},
        ])

        update_custom_formation(user, 'Minha 3-4-3', [
            {'slot_code': 'GK', 'label': 'Goleiro', 'x': 50, 'y': 5, 'order': 0},
            {'slot_code': 'LB', 'label': 'Lateral', 'x': 20, 'y': 25, 'order': 1},
            {'slot_code': 'ST', 'label': 'Atacante', 'x': 70, 'y': 80, 'order': 2},
        ])

        self.assertEqual(
            set(FormationSlot.objects.filter(formation='Minha 3-4-3').values_list('slot_code', flat=True)),
            {'GK', 'LB', 'ST'}
        )

        delete_custom_formation(user, 'Minha 3-4-3')
        self.assertFalse(FormationSlot.objects.filter(formation='Minha 3-4-3').exists())
