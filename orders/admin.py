from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.contrib import messages
from .models import Cart, CartItem, Order, Payment


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'total_price')
    search_fields = ('user__username', 'id')
    list_filter = ('created_at',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity', 'total_price')
    search_fields = ('product__name', 'cart__user__username')
    list_filter = ('cart',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'email', 'total_amount', 'status', 'created_at', 'action_buttons')
    search_fields = ('customer_name', 'email', 'id')
    list_filter = ('status', 'created_at')

    actions = ['approve_orders', 'process_orders', 'ship_orders', 'deliver_orders', 'cancel_orders']

    def action_buttons(self, obj):
        """Add inline action buttons for order status changes."""
        return format_html(
            '<a class="button" href="approve/{}/">✅ Approve</a> '
            '<a class="button" href="process/{}/">🔄 Process</a> '
            '<a class="button" href="ship/{}/">📦 Ship</a> '
            '<a class="button" href="deliver/{}/">🚚 Deliver</a> '
            '<a class="button" href="cancel/{}/" style="color:red;">❌ Cancel</a>',
            obj.id, obj.id, obj.id, obj.id, obj.id
        )
    
    action_buttons.allow_tags = True

    def approve_orders(self, request, queryset):
        """Approve selected orders."""
        updated = queryset.update(status='Processing')
        self.message_user(request, f"{updated} orders approved.")

    def process_orders(self, request, queryset):
        """Move selected orders to processing."""
        updated = queryset.update(status='Processing')
        self.message_user(request, f"{updated} orders are now being processed.")

    def ship_orders(self, request, queryset):
        """Mark selected orders as shipped."""
        updated = queryset.update(status='Shipped')
        self.message_user(request, f"{updated} orders have been shipped.")

    def deliver_orders(self, request, queryset):
        """Mark selected orders as delivered."""
        updated = queryset.update(status='Delivered')
        self.message_user(request, f"{updated} orders have been delivered.")

    def cancel_orders(self, request, queryset):
        """Cancel selected orders."""
        updated = queryset.update(status='Cancelled')
        self.message_user(request, f"{updated} orders have been cancelled.")


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'amount', 'payment_status', 'payment_method', 'refund_action')

    def refund_action(self, obj):
        if obj.payment_status == "Successful" and not obj.refund_status:
            return format_html('<a href="/admin/issue-refund/{}/" style="color: red;">Issue Refund</a>', obj.id)
        return "Refunded" if obj.refund_status else "N/A"

    refund_action.allow_tags = True
    refund_action.short_description = "Refund"

admin.site.register(Payment, PaymentAdmin)