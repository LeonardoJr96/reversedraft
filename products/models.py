from django.db import models

class Product(models.Model):
    player = models.OneToOneField(
        'fifa_data.Player',
        on_delete=models.CASCADE,
        related_name='product',
        null=True, blank=True,   # null=True só durante a migração; depois você pode travar como obrigatório
    )
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=500, blank=True)
    quantity = models.IntegerField(default=1)   # jogador é sempre "1 unidade"
    category = models.CharField(max_length=255, blank=True)  # ex: posição (ST, CB...)
    price = models.DecimalField(max_digits=12, decimal_places=2)  # valor de mercado, usado no modo PLAYER_VALUE do leilão
    date_posted = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        ordering = ['-date_posted']

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    is_cover = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']