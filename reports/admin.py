from django.contrib import admin
from .models import Report, Sales

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'generated_at')
    list_filter = ('report_type', 'generated_at')

@admin.register(Sales)
class SalesAdmin(admin.ModelAdmin):
    list_display = ('product', 'order', 'quantity', 'price', 'sale_date')
    list_filter = ('sale_date', 'product')
    search_fields = ('product__name', 'order__id')
