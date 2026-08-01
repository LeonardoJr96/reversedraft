from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from .models import Product


class ProductImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='admin',
            email='admin@example.com',
            password='StrongPass123!',
            cpf='12345678909',
            cellphone='11999999999',
            address='Rua Teste',
            town='São Paulo',
            post_code='01000-000',
            country='Brasil',
            birth_date='1990-01-01',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_product_with_image_upload(self):
        image_file = BytesIO()
        Image.new('RGB', (1, 1), color='red').save(image_file, format='PNG')
        image_content = image_file.getvalue()
        image = SimpleUploadedFile(
            'test.png',
            image_content,
            content_type='image/png',
        )

        response = self.client.post(
            '/api/v1/products/',
            {
                'title': 'Produto com imagem',
                'description': 'Descrição do produto',
                'price': '10.00',
                'image': image,
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertTrue(Product.objects.filter(title='Produto com imagem').exists())
        product = Product.objects.get(title='Produto com imagem')
        self.assertTrue(product.images.exists())
