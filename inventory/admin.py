from django.contrib import admin
from django.db.models import Sum
from .models import Category, Supplier, Product, Stock, Sale

# ============================
# CATEGORY ADMIN
# ============================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


# ============================
# SUPPLIER ADMIN
# ============================
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_number', 'email')
    search_fields = ('name', 'email')


# ============================
# PRODUCT ADMIN
# ============================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'supplier', 'price', 'get_stock')
    search_fields = ('name', 'sku')
    list_filter = ('category', 'supplier')

    def get_stock(self, obj):
        """Show available stock in admin"""
        return obj.get_available_stock()
    get_stock.short_description = "Available Stock"


# ============================
# STOCK ADMIN
# ============================
@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'low_stock_threshold', 'last_updated')
    search_fields = ('product__name',)
    list_filter = ('last_updated',)

    actions = ['mark_low_stock', 'replenish_stock']

    def mark_low_stock(self, request, queryset):
        """Highlight low-stock items in admin"""
        queryset.update(quantity=5)
    mark_low_stock.short_description = "Set stock to 5 for selected items"

    def replenish_stock(self, request, queryset):
        """Replenish selected stock items"""
        for stock in queryset:
            stock.update_stock(20)
    replenish_stock.short_description = "Add 20 items to selected stock"


# ============================
# SALE ADMIN (Sales Tracking)
# ============================
@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product', 'customer', 'quantity_sold', 'total_price', 'sale_date')
    search_fields = ('product__name', 'customer__username')
    list_filter = ('sale_date', 'product', 'customer')

    actions = ['calculate_revenue', 'get_best_selling_products']

    def calculate_revenue(self, request, queryset):
        """Calculate total revenue from selected sales"""
        total_revenue = queryset.aggregate(Sum('total_price'))['total_price__sum']
        self.message_user(request, f"Total Revenue: ${total_revenue:.2f}")
    calculate_revenue.short_description = "Calculate total revenue"

    def get_best_selling_products(self, request, queryset):
        """Find best-selling products"""
        best_sellers = queryset.values('product__name').annotate(total_sold=Sum('quantity_sold')).order_by('-total_sold')
        msg = ", ".join([f"{item['product__name']} ({item['total_sold']} sold)" for item in best_sellers[:5]])
        self.message_user(request, f"Best-selling products: {msg}")
    get_best_selling_products.short_description = "Show best-selling products"

