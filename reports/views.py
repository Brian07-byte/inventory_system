from django.shortcuts import render
from django.http import JsonResponse
from django.utils.timezone import now
from orders.models import Order, Payment
from inventory.models import Product, Stock
from django.contrib.auth import get_user_model
from .models import Sales, Report

User = get_user_model()

# ----------- JSON API Reports (For API responses) -----------

def sales_report_api(request):
    """Generate a sales report in JSON format including all completed orders."""
    orders = Order.objects.filter(status='Delivered')
    total_sales = sum(order.total_amount for order in orders)

    data = {
        'total_orders': orders.count(),
        'total_sales': total_sales,
        'orders': [
            {
                'id': order.id,
                'customer': order.customer_name,
                'total_amount': order.total_amount,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            } for order in orders
        ]
    }
    return JsonResponse(data)

def stock_report_api(request):
    """Generate a stock report in JSON format."""
    products = Product.objects.all()
    data = {
        'total_products': products.count(),
        'stock_details': [
            {
                'product': product.name,
                'sku': product.sku,
                'available_stock': product.get_available_stock(),
            } for product in products
        ]
    }
    return JsonResponse(data)

def user_report_api(request):
    """Generate a user report in JSON format."""
    users = User.objects.all()
    data = {
        'total_users': users.count(),
        'users': [
            {
                'username': user.username,
                'email': user.email,
                'role': user.get_role_display() if hasattr(user, 'get_role_display') else 'N/A',
                'date_joined': user.date_joined.strftime('%Y-%m-%d')
            } for user in users
        ]
    }
    return JsonResponse(data)

def payment_report_api(request):
    """Generate a payment report in JSON format."""
    payments = Payment.objects.filter(payment_status='Successful')
    total_revenue = sum(payment.amount for payment in payments)

    data = {
        'total_payments': payments.count(),
        'total_revenue': total_revenue,
        'payments': [
            {
                'order_id': payment.order.id,
                'user': payment.user.username if payment.user else 'Guest',
                'amount': payment.amount,
                'payment_method': payment.payment_method,
                'payment_date': payment.payment_date.strftime('%Y-%m-%d %H:%M:%S')
            } for payment in payments
        ]
    }
    return JsonResponse(data)

# ----------- HTML Reports (For web page display) -----------

def sales_report_page(request):
    """Generate a sales report in HTML format."""
    sales = Sales.objects.all()
    total_revenue = sum(sale.total_sale_value() for sale in sales)
    return render(request, 'report/sales_report.html', {'sales': sales, 'total_revenue': total_revenue})

def stock_report_page(request):
    """Generate a stock report in HTML format."""
    stocks = Stock.objects.all()
    return render(request, 'report/stock_report.html', {'stocks': stocks})

def user_report_page(request):
    """Generate a user report in HTML format."""
    users = User.objects.all()
    return render(request, 'report/user_report.html', {'users': users})

def payment_report_page(request):
    """Generate a payment report in HTML format."""
    payments = Payment.objects.all()
    total_payments = sum(payment.amount for payment in payments)
    return render(request, 'report/payment_report.html', {'payments': payments, 'total_payments': total_payments})

def product_report_page(request):
    """Generate a product report in HTML format."""
    products = Product.objects.all()
    return render(request, 'report/product_report.html', {'products': products})
