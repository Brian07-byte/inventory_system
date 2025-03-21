from django.urls import path
from . import views
from .views import process_payment, payment_history, admin_payment_list
from .views import export_orders_csv, export_orders_excel,generate_invoice,order_report,generate_order_report_pdf
from .views import admin_order_list, admin_order_detail, update_order_status, delete_order
from .views import my_orders


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


     path('my-orders/', my_orders, name='my_orders'),


     ##Admin order managemnt
     path('admin/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
     path('admin/orders/', admin_order_list, name='admin_order_list'),
    path('admin/orders/<int:order_id>/', admin_order_detail, name='admin_order_detail'),
    path('admin/orders/<int:order_id>/update/', update_order_status, name='update_order_status'),
    path('admin/orders/<int:order_id>/delete/', delete_order, name='delete_order'),
    
    ###reports
    path("export/csv/", export_orders_csv, name="export_orders_csv"),
    path("export/excel/", export_orders_excel, name="export_orders_excel"),
    path("invoice/<int:order_id>/", generate_invoice, name="generate_invoice"),
    
    path('order-report/', order_report, name='order_report'),
    path('order-report/download/', generate_order_report_pdf, name='generate_order_report_pdf'),
    
    ######3payments
    path("payment/<int:order_id>/", process_payment, name="process_payment"),
    path("payment-history/", payment_history, name="payment_history"),
    path("admin/payments/", admin_payment_list, name="admin_payment_list"),

]
