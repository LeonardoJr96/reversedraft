from rest_framework import serializers
from .models import Product, ProductImage
from fifa_data.serializers import PlayerSerializer

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_cover', 'order']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, required=False)
    image = serializers.ImageField(write_only=True, required=False)
    player = PlayerSerializer(read_only=True)   # dados completos do jogador, só leitura

    class Meta:
        model = Product
        fields = ['id', 'player', 'title', 'description', 'quantity', 'category', 'price', 'date_posted', 'images', 'image']

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        uploaded_image = validated_data.pop('image', None)
        product = Product.objects.create(**validated_data)

        if uploaded_image:
            ProductImage.objects.create(product=product, image=uploaded_image)

        for image_data in images_data:
            ProductImage.objects.create(product=product, **image_data)
        return product

    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', None)
        uploaded_image = validated_data.pop('image', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if uploaded_image:
            ProductImage.objects.create(product=instance, image=uploaded_image)
        if images_data is not None:
            for image_data in images_data:
                ProductImage.objects.create(product=instance, **image_data)
        return instance