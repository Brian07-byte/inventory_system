from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

# Category model
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


# Supplier model
class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


# Product model
class Product(models.Model):
    name = models.CharField(max_length=100)
    sku = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_available_stock(self):
        """Calculate total stock from Stock model"""
        total_stock = self.stock_entries.aggregate(models.Sum('quantity'))['quantity__sum']
        return total_stock if total_stock else 0  # Return 0 if None


# Stock model
class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_entries')
    quantity = models.PositiveIntegerField()
    low_stock_threshold = models.PositiveIntegerField(default=10)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.product.name} - {self.quantity} in stock'

    def update_stock(self, quantity):
        """Increase stock quantity"""
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        self.quantity += quantity
        self.save()

    def reduce_stock(self, quantity):
        """Decrease stock quantity safely"""
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")

        if self.quantity >= quantity:
            self.quantity -= quantity
            self.save()
        else:
            raise ValidationError(f"Not enough stock available for {self.product.name}.")

    def is_low_stock(self):
        """Check if stock is below the threshold"""
        return self.quantity <= self.low_stock_threshold


# Automatically create a stock entry for new products
@receiver(post_save, sender=Product)
def create_stock_entry(sender, instance, created, **kwargs):
    if created:
        Stock.objects.create(product=instance, quantity=10)  # Default initial stock
