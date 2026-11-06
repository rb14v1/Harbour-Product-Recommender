from django.contrib import admin

from apps.products.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "category", "price", "created_at"]
    list_filter = ["category"]
    search_fields = ["name", "description"]
