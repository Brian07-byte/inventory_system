from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from inventory.models import Product
from users.models import *
from django.db.models import Sum, F

# Cart model
class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        """Calculate total price of all cart items."""
        return sum(item.total_price() for item in self.cart_items.all())

    def clear_cart(self):
        """Clear the cart after order placement."""
        self.cart_items.all().delete()

    def __str__(self):
        return f"Cart {self.id} - User: {self.user.username if self.user else 'Guest'}"


# Cart Item model
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        """Calculate total price for this cart item."""
        return self.product.price * self.quantity

    def save(self, *args, **kwargs):
        """Check available stock before saving."""
        stock_entry = self.product.stock_entries.first()
        if not stock_entry or stock_entry.quantity < self.quantity:
            raise ValidationError(f"Not enough stock available for {self.product.name}.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Cart ID: {self.cart.id})"
    


class Order(models.Model):
    """Represents an order placed by a customer, tracking order details, status, and payments."""
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Paid', 'Paid'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Refunded', 'Refunded'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    cart = models.ForeignKey(
        'Cart', on_delete=models.SET_NULL, null=True, blank=True
    )  # Preserve cart history
    customer_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    email = models.EmailField()
    address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    delivered_at = models.DateTimeField(null=True, blank=True)  # Track delivery date
    payment_status = models.BooleanField(default=False)  # True if payment is received

    def save(self, *args, **kwargs):
        """
        Override save method to ensure stock validation before saving a new order.
        If it's a new order, it will validate stock, reduce inventory, and clear the cart.
        """
        is_new = self._state.adding  # Check if it's a new order

        if is_new and self.cart:
            if not self.validate_stock():
                raise ValidationError("🚨 Order cannot be placed due to insufficient stock.")
            
            super().save(*args, **kwargs)  # Save first to generate Order ID
            self.reduce_stock()
            self.cart.clear_cart()  # Clear cart after order placement
        else:
            super().save(*args, **kwargs)  # Normal updates

    def validate_stock(self):
        """Check if all products in the cart have sufficient stock before placing the order."""
        if not self.cart:
            return False

        for cart_item in self.cart.cart_items.select_related('product'):
            stock_entry = cart_item.product.stock_entries.first()
            if not stock_entry or stock_entry.quantity < cart_item.quantity:
                return False  # Not enough stock
        return True

    def reduce_stock(self):
        """Reduce stock safely using Django's F() expressions to prevent race conditions."""
        if not self.cart:
            return

        for cart_item in self.cart.cart_items.select_related('product'):
            stock_entry = cart_item.product.stock_entries.first()
            if stock_entry:
                stock_entry.quantity = F('quantity') - cart_item.quantity
                stock_entry.save(update_fields=['quantity'])
            else:
                raise ValidationError(f"🚨 No stock entry found for {cart_item.product.name}.")

    def __str__(self):
        return f"Order {self.id} - {self.customer_name} ({self.status})"

    # ✅ **Improved Reporting Methods**
    @classmethod
    def total_sales(cls):
        """Get total revenue from successfully delivered orders."""
        return cls.objects.filter(status="Delivered", payment_status=True).aggregate(
            total_sales=Sum("total_amount")
        )["total_sales"] or 0

    @classmethod
    def total_orders(cls):
        """Get the total count of delivered orders."""
        return cls.objects.filter(status="Delivered").count()

    @classmethod
    def sales_per_product(cls):
        """Get total sales per product (for dashboard analytics)."""
        return (
            cls.objects.filter(status="Delivered", cart__cart_items__product__isnull=False)
            .values(product_name=F("cart__cart_items__product__name"))
            .annotate(total_sold=Sum("cart__cart_items__quantity"))
            .order_by("-total_sold")
        )

    @classmethod
    def sales_per_customer(cls):
        """Get total spending per customer for analytics."""
        return (
            cls.objects.filter(status="Delivered", user__isnull=False)
            .values(customer=F("user__username"))
            .annotate(total_spent=Sum("total_amount"))
            .order_by("-total_spent")
        )

    @classmethod
    def total_revenue(cls):
        """Calculate total revenue from all completed and paid orders."""
        return cls.objects.filter(status="Delivered", payment_status=True).aggregate(
            total_revenue=Sum("total_amount")
        )["total_revenue"] or 0    


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('MPesa', 'MPesa'),
        ('Credit Card', 'Credit Card'),
        ('PayPal', 'PayPal'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.BooleanField(default=False)  # True = Paid, False = Unpaid/Refunded
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)

    def save(self, *args, **kwargs):
        """Automatically update the Order status if payment is successful."""
        if self.payment_status:  # If Paid
            self.order.status = "Processing"
        else:  # If not paid or refunded
            self.order.status = "Refunded"

        self.order.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment for Order {self.order.id} - {'Paid' if self.payment_status else 'Pending'}"
