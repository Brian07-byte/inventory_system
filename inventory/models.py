from django.db import models, transaction
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils.timezone import now, timedelta
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

# ===========================
# CATEGORY MODEL
# ===========================
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


# ===========================
# SUPPLIER MODEL
# ===========================
class Supplier(models.Model):
    supplier_code = models.CharField(max_length=50, unique=True, blank=True)  # Unique supplier code
    name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)  # Active status
    date_added = models.DateTimeField(auto_now_add=True)  # Track supplier creation date
    products = models.ManyToManyField('Product', related_name='suppliers', blank=True)  # ✅ Link to Products

    def __str__(self):
        return f"{self.supplier_code} - {self.name}"

    def get_products(self):
        """Retrieve all products supplied by this supplier."""
        return self.products.all()

    def save(self, *args, **kwargs):
        """Auto-generate supplier code in an atomic transaction to prevent duplication."""
        if not self.supplier_code:
            with transaction.atomic():  # ✅ Ensure uniqueness
                last_supplier = Supplier.objects.select_for_update().order_by('-id').first()
                next_id = (last_supplier.id + 1) if last_supplier else 1
                self.supplier_code = f"SUP-{str(next_id).zfill(3)}"
        super().save(*args, **kwargs)

# ===========================
# PRODUCT MODEL
# ===========================
class Product(models.Model):
    name = models.CharField(max_length=100)
    sku = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="supplied_products")
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_available_stock(self):
        """Calculate total available stock for this product"""
        total_stock = self.stock_entries.aggregate(total_stock=Sum('quantity'))['total_stock']
        return total_stock or 0


# ===========================
# STOCK MODEL
# ===========================
class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_entries')
    quantity = models.PositiveIntegerField()
    low_stock_threshold = models.PositiveIntegerField(default=10)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.product.name} - {self.quantity} in stock'

    def update_stock(self, quantity):
        """Increase stock quantity safely"""
        if quantity < 0:
            raise ValidationError("Quantity cannot be negative")
        self.quantity += quantity
        self.save()

    def reduce_stock(self, quantity):
        """Decrease stock quantity safely"""
        if quantity < 0:
            raise ValidationError("Quantity cannot be negative")

        if self.quantity >= quantity:
            self.quantity -= quantity
            self.save()
        else:
            raise ValidationError(f"Not enough stock for {self.product.name}. Available: {self.quantity}, Requested: {quantity}")

    def is_low_stock(self):
        """Check if stock is below the threshold"""
        return self.quantity <= self.low_stock_threshold


# Automatically create a stock entry for new products
@receiver(post_save, sender=Product)
def create_stock_entry(sender, instance, created, **kwargs):
    if created:
        Stock.objects.create(product=instance, quantity=10)  # Default initial stock


class Sale(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='sales')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    quantity_sold = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.username if self.customer else 'Guest'} - {self.quantity_sold} x {self.product.name} on {self.sale_date.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
        """Reduce stock when a sale is made and ensure stock updates correctly."""
        stock_entry = Stock.objects.filter(product=self.product).first()

        if not stock_entry:
            raise ValidationError(f"Stock entry not found for {self.product.name}.")

        print(f"Attempting to sell {self.quantity_sold} of {self.product.name}. Available stock: {stock_entry.quantity}")

        if stock_entry.quantity >= self.quantity_sold:
            stock_entry.reduce_stock(self.quantity_sold)
            super().save(*args, **kwargs)
            print(f"✅ Sale for {self.product.name} recorded successfully!")
        else:
            raise ValidationError(f"❌ Not enough stock for {self.product.name}. Available: {stock_entry.quantity}, Requested: {self.quantity_sold}")

    # ==============================
    # COMPREHENSIVE SALES ANALYSIS
    # ==============================

    @staticmethod
    def get_total_revenue():
        """Calculate total revenue from all sales."""
        return Sale.objects.aggregate(total_revenue=Sum('total_price'))['total_revenue'] or 0

    @staticmethod
    def get_total_sales_today():
        """Calculate total sales for today."""
        today = now().date()
        return Sale.objects.filter(sale_date__date=today).aggregate(total_sales=Sum('total_price'))['total_sales'] or 0

    @staticmethod
    def get_total_sales_week():
        """Calculate total sales for the current week."""
        start_of_week = now().date() - timedelta(days=now().weekday())  # Monday of this week
        return Sale.objects.filter(sale_date__date__gte=start_of_week).aggregate(total_sales=Sum('total_price'))['total_sales'] or 0

    @staticmethod
    def get_total_sales_month():
        """Calculate total sales for the current month."""
        start_of_month = now().replace(day=1)  # First day of the month
        return Sale.objects.filter(sale_date__date__gte=start_of_month).aggregate(total_sales=Sum('total_price'))['total_sales'] or 0

    @staticmethod
    def get_total_sales_year():
        """Calculate total sales for the current year."""
        start_of_year = now().replace(month=1, day=1)  # First day of the year
        return Sale.objects.filter(sale_date__date__gte=start_of_year).aggregate(total_sales=Sum('total_price'))['total_sales'] or 0

    @staticmethod
    def get_best_selling_products():
        """Retrieve best-selling products by total quantity sold (all-time)."""
        return (
            Sale.objects.values('product__name')
            .annotate(total_sold=Sum('quantity_sold'))
            .order_by('-total_sold')
        )

    @staticmethod
    def get_best_selling_products_today():
        """Retrieve best-selling products today."""
        today = now().date()
        return (
            Sale.objects.filter(sale_date__date=today)
            .values('product__name')
            .annotate(total_sold=Sum('quantity_sold'))
            .order_by('-total_sold')
        )

    @staticmethod
    def get_best_selling_products_week():
        """Retrieve best-selling products for the current week."""
        start_of_week = now().date() - timedelta(days=now().weekday())
        return (
            Sale.objects.filter(sale_date__date__gte=start_of_week)
            .values('product__name')
            .annotate(total_sold=Sum('quantity_sold'))
            .order_by('-total_sold')
        )

    @staticmethod
    def get_best_selling_products_month():
        """Retrieve best-selling products for the current month."""
        start_of_month = now().replace(day=1)
        return (
            Sale.objects.filter(sale_date__date__gte=start_of_month)
            .values('product__name')
            .annotate(total_sold=Sum('quantity_sold'))
            .order_by('-total_sold')
        )

    @staticmethod
    def get_sales_by_day():
        """Get total sales per day for the last 30 days."""
        start_date = now().date() - timedelta(days=30)
        return (
            Sale.objects.filter(sale_date__date__gte=start_date)
            .extra({'day': "DATE(sale_date)"})
            .values('day')
            .annotate(total_sales=Sum('total_price'))
            .order_by('day')
        )

    @staticmethod
    def get_sales_by_week():
        """Get total sales per week for the last 12 weeks."""
        start_date = now().date() - timedelta(weeks=12)
        return (
            Sale.objects.filter(sale_date__date__gte=start_date)
            .extra({'week': "strftime('%%Y-%%W', sale_date)"})  # Format: Year-Week
            .values('week')
            .annotate(total_sales=Sum('total_price'))
            .order_by('week')
        )

    @staticmethod
    def get_sales_by_month():
        """Get total sales per month for the last 12 months."""
        start_date = now().date() - timedelta(days=365)
        return (
            Sale.objects.filter(sale_date__date__gte=start_date)
            .extra({'month': "strftime('%%Y-%%m', sale_date)"})  # Format: YYYY-MM
            .values('month')
            .annotate(total_sales=Sum('total_price'))
            .order_by('month')
        )

    @staticmethod
    def get_sales_by_year():
        """Get total sales per year for the last 5 years."""
        start_date = now().date() - timedelta(days=365 * 5)
        return (
            Sale.objects.filter(sale_date__date__gte=start_date)
            .extra({'year': "strftime('%%Y', sale_date)"})  # Format: YYYY
            .values('year')
            .annotate(total_sales=Sum('total_price'))
            .order_by('year')
        )
        
        
        from django.db import models
from django.conf import settings
from django.utils.timezone import now

class Notification(models.Model):
    EVENT_CHOICES = [
        ('stock_added', 'Stock Added'),
        ('stock_low', 'Stock Low'),
        ('order_placed', 'Order Placed'),
        ('order_shipped', 'Order Shipped'),
        ('order_delivered', 'Order Delivered'),
        ('new_user', 'New User Signup'),
        ('payment_success', 'Payment Successful'),
        ('payment_failed', 'Payment Failed'),
        ('review_added', 'New Review'),
        ('out_of_stock', 'Product Out of Stock'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    event = models.CharField(max_length=20, choices=EVENT_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(default=now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_event_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
