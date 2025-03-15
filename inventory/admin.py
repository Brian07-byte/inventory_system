from django.contrib import admin
from .models import Product, Category, Supplier, Stock


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_number', 'email', 'address')
    search_fields = ('name', 'email', 'contact_number')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'supplier', 'price', 'available_stock')
    search_fields = ('name', 'sku', 'category__name', 'supplier__name')
    list_filter = ('category', 'supplier')
    
    def available_stock(self, obj):
        """Shows stock levels in the product list"""
        return obj.available_stock

    available_stock.short_description = "Available Stock"


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'low_stock_threshold', 'last_updated')
    search_fields = ('product__name',)
    list_filter = ('last_updated',)
