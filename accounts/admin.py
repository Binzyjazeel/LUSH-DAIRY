from django.contrib import admin
from .models import Product


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_blocked', 'is_listed', 'created_at')
    list_editable = ('is_blocked', 'is_listed')
    list_filter = ('is_blocked', 'is_listed', 'category')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)

admin.site.register(Product, ProductAdmin)
