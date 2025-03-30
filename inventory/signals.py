from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Notification, Product
from .models import *
from inventory.models import *
from orders.models import *

CustomUser = settings.AUTH_USER_MODEL

# New User Signup
@receiver(post_save, sender=CustomUser)
def notify_new_user_signup(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance,
            event="new_user",
            message=f"New user {instance.username} has signed up."
        )

# Stock Added
@receiver(post_save, sender=Product)
def notify_stock_added(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            event="stock_added",
            message=f"New stock added: {instance.name} (Qty: {instance.quantity})"
        )

# Stock Low Warning
@receiver(post_save, sender=Product)
def notify_stock_low(sender, instance, **kwargs):
    if instance.quantity < 5:
        Notification.objects.create(
            event="stock_low",
            message=f"Stock running low for {instance.name}. Only {instance.quantity} left!"
        )

# Product Out of Stock
@receiver(post_save, sender=Product)
def notify_out_of_stock(sender, instance, **kwargs):
    if instance.quantity == 0:
        Notification.objects.create(
            event="out_of_stock",
            message=f"{instance.name} is out of stock!"
        )

# New Order Placed
@receiver(post_save, sender=Order)
def notify_order_placed(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.user,
            event="order_placed",
            message=f"Order #{instance.id} has been placed by {instance.user.username}."
        )

# Order Shipped
@receiver(post_save, sender=Order)
def notify_order_shipped(sender, instance, **kwargs):
    if instance.status == 'shipped':
        Notification.objects.create(
            user=instance.user,
            event="order_shipped",
            message=f"Your order #{instance.id} has been shipped."
        )

# Order Delivered
@receiver(post_save, sender=Order)
def notify_order_delivered(sender, instance, **kwargs):
    if instance.status == 'delivered':
        Notification.objects.create(
            user=instance.user,
            event="order_delivered",
            message=f"Your order #{instance.id} has been delivered!"
        )

# Payment Success
@receiver(post_save, sender=Payment)
def notify_payment_success(sender, instance, created, **kwargs):
    if created and instance.status == 'success':
        Notification.objects.create(
            user=instance.user,
            event="payment_success",
            message=f"Payment for order #{instance.order.id} was successful."
        )

# Payment Failed
@receiver(post_save, sender=Payment)
def notify_payment_failed(sender, instance, **kwargs):
    if instance.status == 'failed':
        Notification.objects.create(
            user=instance.user,
            event="payment_failed",
            message=f"Payment for order #{instance.order.id} failed!"
        )


