from django.db import models
from django.utils.timezone import now
from orders.models import Order, Payment
from inventory.models import Product, Stock
from django.contrib.auth import get_user_model

User = get_user_model()

class Sales(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='sales')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateTimeField(default=now)

    def __str__(self):
        return f"Sale of {self.product.name} - {self.quantity} units"

    def total_sale_value(self):
        return self.quantity * self.price

class Report(models.Model):
    REPORT_TYPES = [
        ('sales', 'Sales Report'),
        ('stock', 'Stock Report'),
        ('user', 'User Report'),
        ('payment', 'Payment Report'),
        ('product', 'Product Report'),
    ]

    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}"
