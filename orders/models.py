from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from inventory.models import Product

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
        stock_entry = self.product.stock_entries.first()  # Get stock entry
        if not stock_entry or stock_entry.quantity < self.quantity:
            raise ValidationError(f"Not enough stock available for {self.product.name}.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Cart ID: {self.cart.id})"
    
    


# Order model
class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True, blank=True)  # Preserve cart history
    customer_name = models.CharField(max_length=255)
    email = models.EmailField()
    address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Override save to validate stock and reduce it before creating the order."""
        if self._state.adding and self.cart:  # Ensure this is a new order and cart exists
            if not self.validate_stock():
                raise ValidationError("Order cannot be placed due to insufficient stock.")
            super().save(*args, **kwargs)
            self.reduce_stock()
            if self.cart:
                self.cart.clear_cart()  # Clear the cart after placing an order
        else:
            super().save(*args, **kwargs)  # Allow normal updates (status changes)

    def validate_stock(self):
        """Check if all products in the cart have enough stock."""
        if self.cart:
            for cart_item in self.cart.cart_items.all():
                stock_entry = cart_item.product.stock_entries.first()
                if not stock_entry or stock_entry.quantity < cart_item.quantity:
                    return False
        return True

    def reduce_stock(self):
        """Reduce available stock quantity for each ordered product."""
        if self.cart:
            for cart_item in self.cart.cart_items.all():
                stock_entry = cart_item.product.stock_entries.first()
                if stock_entry:
                    stock_entry.reduce_stock(cart_item.quantity)
                else:
                    raise ValidationError(f"No stock entry found for {cart_item.product.name}.")

    def __str__(self):
        return f"Order {self.id} - {self.customer_name}"


class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Successful', 'Successful'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded')
    ], default='Pending')
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, choices=[
        ('MPesa', 'MPesa'),
        ('Credit Card', 'Credit Card'),
        ('PayPal', 'PayPal')
    ])
    refund_status = models.BooleanField(default=False)  # Indicates if a refund was issued

    def save(self, *args, **kwargs):
        """If payment is successful, mark order as 'Processing' and reduce stock."""
        if self.payment_status == "Successful":
            self.order.status = "Processing"
            self.order.save()

        super().save(*args, **kwargs)

    def issue_refund(self):
        """Mark payment as refunded and update order status."""
        if self.payment_status == "Successful" and not self.refund_status:
            self.payment_status = "Refunded"
            self.refund_status = True
            self.order.status = "Refunded"
            self.order.save()
            self.save()
            return True
        return False

    def __str__(self):
        return f"Payment for Order {self.order.id} - {self.payment_status}"