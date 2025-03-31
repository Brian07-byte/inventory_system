from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import *
from inventory.models import *
from orders.models import *

User = get_user_model()  # Ensures compatibility with custom User models

### 📢 ADMIN NOTIFICATIONS
# ✅ New User Signup
@receiver(post_save, sender=User)
def notify_admin_new_user(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            event="new_user",
            message=f"New user {instance.username} has signed up."
        )

# ✅ Stock Added
@receiver(post_save, sender=Product)
def notify_admin_stock_added(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            event="stock_added",
            message=f"New stock added: {instance.name} (Qty: {instance.quantity})"
        )

# ✅ Low Stock Warning
@receiver(post_save, sender=Product)
def notify_admin_stock_low(sender, instance, **kwargs):
    if instance.quantity < 5:
        Notification.objects.create(
            event="stock_low",
            message=f"⚠️ Low stock: {instance.name}. Only {instance.quantity} left!"
        )

# ✅ Out of Stock
@receiver(post_save, sender=Product)
def notify_admin_out_of_stock(sender, instance, **kwargs):
    if instance.quantity == 0:
        Notification.objects.create(
            event="out_of_stock",
            message=f"🚨 {instance.name} is out of stock!"
        )

# ✅ New Order Placed
@receiver(post_save, sender=Order)
def notify_admin_order_placed(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            event="order_placed",
            message=f"🛒 Order #{instance.id} placed by {instance.user.username}."
        )

# ✅ Payment Successful
@receiver(post_save, sender=Payment)
def notify_admin_payment_success(sender, instance, created, **kwargs):
    if created and instance.payment_status:
        Notification.objects.create(
            event="payment_success",
            message=f"💰 Payment for order #{instance.order.id} was successful."
        )

# ✅ Payment Failed
@receiver(post_save, sender=Payment)
def notify_admin_payment_failed(sender, instance, **kwargs):
    if not instance.payment_status:
        Notification.objects.create(
            event="payment_failed",
            message=f"❌ Payment for order #{instance.order.id} failed!"
        )


### 📢 CUSTOMER NOTIFICATIONS
# ✅ Order Shipped
@receiver(post_save, sender=Order)
def notify_customer_order_shipped(sender, instance, **kwargs):
    if instance.status == 'shipped':
        Notification.objects.create(
            user=instance.user,
            event="order_shipped",
            message=f"🚚 Your order #{instance.id} has been shipped!"
        )

# ✅ Order Delivered
@receiver(post_save, sender=Order)
def notify_customer_order_delivered(sender, instance, **kwargs):
    if instance.status == 'delivered':
        Notification.objects.create(
            user=instance.user,
            event="order_delivered",
            message=f"🎉 Your order #{instance.id} has been delivered!"
        )

# ✅ New Product Alert
@receiver(post_save, sender=Product)
def notify_customer_new_product(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            event="new_product",
            message=f"🆕 New product available: {instance.name}!"
        )
