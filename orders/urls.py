from django.urls import path
from . import views
from .views import admin_order_list, admin_order_detail, update_order_status, delete_order
from .views import payment_view,my_orders
from .views import manage_payments, payment_details, issue_refund, customer_payments, request_refund

app_name = 'orders'

urlpatterns = [
    # Cart views
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),  # Add product to cart
    path('view/', views.cart_detail, name='cart_detail'),  # View cart details
    path('update/<int:cart_item_id>/', views.update_cart_item, name='update_cart_item'),  # Update cart item quantity
    path('remove/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),  # Remove item from cart
    
    # Checkout and Order views
    path('checkout/', views.checkout_view, name='checkout_view'),  # Checkout view to place an order
    path('order_confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),  # View order confirmation

    path("payment/<int:order_id>/", payment_view, name="payment"),

     path('my-orders/', my_orders, name='my_orders'),


     ##Admin order managemnt
     path('admin/orders/', admin_order_list, name='admin_order_list'),
    path('admin/orders/<int:order_id>/', admin_order_detail, name='admin_order_detail'),
    path('admin/orders/<int:order_id>/update/', update_order_status, name='update_order_status'),
    path('admin/orders/<int:order_id>/delete/', delete_order, name='delete_order'),
    
         # Admin URLs
    path('admin/manage/', manage_payments, name='manage_payments'),
    path('admin/payment/<int:payment_id>/', payment_details, name='payment_details'),
    path('admin/refund/<int:payment_id>/', issue_refund, name='issue_refund'),

    # Customer URLs
    path('my-payments/', customer_payments, name='customer_payments'),
    path('request-refund/<int:payment_id>/', request_refund, name='request_refund'),
]
