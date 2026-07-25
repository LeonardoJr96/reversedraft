from django.contrib import admin
from .models import Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'title', 'price', 'quantity', 'category', 'date_posted']
    search_fields = ['title', 'category', 'player__common_name']
    inlines = [ProductImageInline]