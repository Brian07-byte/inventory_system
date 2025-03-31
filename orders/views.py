from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, F
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
from reportlab.pdfgen import canvas
from django.utils.timezone import make_naive
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Cart, CartItem, Order
from inventory.models import Product
from .forms import *
from django.db.models import Sum, Count
from django.utils.timezone import make_naive
from .models import Payment
from django.db import transaction

def is_admin(user):
    return user.is_staff

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))  # Default quantity is 1

    # Get or create a cart for the current user
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Get or create cart item
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    # Check available stock before adding to cart
    if product.get_available_stock() < cart_item.quantity + quantity:
        messages.error(request, 'Not enough available stock for this product.')
        return redirect('order:cart_detail')

    # Update quantity and save
    cart_item.quantity += quantity
    cart_item.save()

    messages.success(request, f'✅ {product.name} has been added to your cart.')
    return redirect('order:cart_detail')

@login_required
def cart_detail(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = None  # Handle empty cart case

    total_price = cart.total_price() if cart else 0  # Ensure total_price works

    return render(request, 'cart/cart_detail.html', {'cart': cart, 'total_price': total_price})

@login_required
def update_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    quantity = int(request.POST.get('quantity', cart_item.quantity))

    # Prevent zero or negative quantity
    if quantity <= 0:
        messages.error(request, '❌ Quantity must be greater than 0.')
        return redirect('order:cart_detail')

    # Check available stock before updating
    if cart_item.product.get_available_stock() < quantity:
        messages.error(request, '❌ Not enough stock available for this product.')
        return redirect('order:cart_detail')

    cart_item.quantity = quantity
    cart_item.save()
    messages.success(request, f'✏️ Updated quantity for {cart_item.product.name}.')
    return redirect('order:cart_detail')

@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    cart_item.delete()
    messages.success(request, f'🗑️ {cart_item.product.name} has been removed from your cart.')
    return redirect('order:cart_detail')

@login_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)

    # Ensure cart is not empty
    if not cart.cart_items.exists():
        messages.error(request, "❌ Your cart is empty.")
        return redirect('order:cart_detail')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            with transaction.atomic():  # Ensure atomic transaction
                order = form.save(commit=False)
                order.user = request.user
                order.cart = cart
                order.total_amount = cart.total_price()
                order.save()

                # Reduce available stock
                for cart_item in cart.cart_items.select_related('product'):
                    product = cart_item.product
                    quantity = cart_item.quantity

                    if product.get_available_stock() >= quantity:
                        product.stock_entries.update(quantity=product.get_available_stock() - quantity)
                    else:
                        messages.error(request, f"❌ Not enough stock for {product.name}. Order cannot be placed.")
                        return redirect('order:cart_detail')

                # Clear the cart after successful checkout
                cart.clear_cart()

                messages.success(request, "✅ Order placed successfully! Proceed to payment.")
                return redirect('order:process_payment', order_id=order.id)

    else:
        form = OrderForm()

    return render(request, 'cart/checkout.html', {'form': form})

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'cart/order_summary.html', {'order': order})

# ✅ Check if User is Admin

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from orders.models import Order, Payment
import logging

# Set up logging
logger = logging.getLogger(__name__)

@login_required
def process_payment(request, order_id):
    """Handles payment processing with MPesa, Credit Card, or PayPal"""
    
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == "POST":
        payment_method = request.POST.get("payment_method")
        mpesa_code = request.POST.get("mpesa_code", "").strip()  # Only for MPesa
        card_number = request.POST.get("card_number", "").strip()  # For Credit Card / PayPal
        
        # Ensure order is unpaid before proceeding
        if order.payment_status:
            messages.error(request, "This order is already paid.")
            return redirect("orders:cart_detail")  # Redirect to cart details if already paid
        
        # **MPesa Payment Validation**
        if payment_method == "MPesa":
            if not mpesa_code or len(mpesa_code) < 6:
                messages.error(request, "Invalid MPesa transaction code.")
                return redirect("orders:process_payment", order_id=order.id)
            payment_details = f"MPesa Code: {mpesa_code}"
        
        # **Credit Card / PayPal Validation**
        elif payment_method in ["Credit Card", "PayPal"]:
            if not card_number or len(card_number) < 12:
                messages.error(request, "Invalid card number.")
                return redirect("orders:process_payment", order_id=order.id)
            payment_details = f"Card Number: **** **** **** {card_number[-4:]}"

        else:
            messages.error(request, "Invalid payment method.")
            return redirect("orders:process_payment", order_id=order.id)
        
        # **Check if Payment Already Exists**
        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={  # Only set these values if it's a new payment
                "user": request.user,
                "amount": order.total_amount,
                "payment_status": True,  # Mark as Paid
                "payment_method": payment_method,
            }
        )

        if not created:
            # Update existing payment instead of creating a duplicate
            payment.user = request.user
            payment.amount = order.total_amount
            payment.payment_status = True  # Mark as Paid
            payment.payment_method = payment_method
            payment.save()

        # Update Order Status
        order.payment_status = True
        order.status = "Processing"
        order.save()

        # Log the transaction
        logger.info(f"Payment successful - Order {order.id}, User {request.user.username}, Method: {payment_method}, Details: {payment_details}")

        messages.success(request, f"Payment successful! {payment_details}")
        return redirect("orders:order_confirmation", order_id=order.id)  # Redirect after successful payment
    
    return render(request, "payments/payment_form.html", {"order": order})

@login_required
def payment_history(request):
    """Displays payment history for logged-in users."""
    payments = Payment.objects.filter(user=request.user)
    return render(request, "payments/payment_history.html", {"payments": payments})

@login_required
def admin_payment_list(request):
    """Admin view for all payments."""
    if not request.user.is_superuser:
        messages.error(request, "Access Denied!")
        return redirect("home")

    payments = Payment.objects.all()
    return render(request, "payments/admin_payment_list.html", {"payments": payments})


@login_required
def my_orders(request):
    """Display logged-in user's orders with more details."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Collect additional information for each order if needed
    order_details = []
    for order in orders:
        order_info = {
            'order': order,
            'cart_items': order.cart.cart_items.all() if order.cart else [],  # Include cart items if available
            'delivery_date': order.delivered_at if order.status == 'Delivered' else None,
            'payment_status': 'Paid' if order.payment_status else 'Pending',
            'order_total': order.total_amount,
            'order_status': order.status
        }
        order_details.append(order_info)

    return render(request, 'cart/my_orders.html', {'order_details': order_details})


@staff_member_required
def admin_order_list(request):
    """Displays all orders in the admin dashboard with search & filters."""
    orders = Order.objects.all().order_by('-created_at')

    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)

    # Search by order ID or username
    search_query = request.GET.get('search')
    if search_query:
        orders = orders.filter(id__icontains=search_query) | orders.filter(user__username__icontains=search_query)

    return render(request, 'admin/admin_order_list.html', {'orders': orders, 'status_filter': status_filter, 'search_query': search_query})

@staff_member_required
def admin_order_detail(request, order_id):
    """Displays details of a specific order."""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'admin/admin_order_detail.html', {'order': order})

@staff_member_required
def update_order_status(request, order_id):
    """Allows admins to update the status of an order."""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f"✅ Order {order.id} status updated to {new_status}.")
        else:
            messages.error(request, "❌ Invalid status selected.")

        return redirect('orders:admin_order_detail', order_id=order.id)

    return render(request, 'admin/update_order_status.html', {'order': order, 'status_choices': Order.STATUS_CHOICES})

@staff_member_required
def delete_order(request, order_id):
    """Allows admin to delete an order with confirmation."""
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        order.delete()
        messages.success(request, f"🗑️ Order {order.id} has been deleted successfully.")
        return redirect('admin_order_list')

    return render(request, 'admin/delete_order.html', {'order': order})


############orders reports
def sales_dashboard(request):
    """Generate sales statistics for the dashboard."""
    context = {
        "total_sales": Order.total_sales(),
        "total_revenue": Order.total_revenue(),
        "total_orders": Order.total_orders(),
        "sales_by_product": list(Order.sales_per_product()),
        "sales_by_customer": list(Order.sales_per_customer()),
    }
    return render(request, "sales/sales_dashboard.html", context)

def get_daily_sales():
    """Get today's total sales revenue."""
    today = now().date()
    return Order.objects.filter(created_at__date=today, status="Delivered", payment_status=True).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

def get_weekly_sales():
    """Get sales for the past 7 days."""
    last_week = now().date() - timedelta(days=7)
    return Order.objects.filter(created_at__date__gte=last_week, status="Delivered", payment_status=True).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

def get_monthly_sales():
    """Get sales for the current month."""
    first_day_of_month = now().replace(day=1)
    return Order.objects.filter(created_at__date__gte=first_day_of_month, status="Delivered", payment_status=True).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

def get_yearly_sales():
    """Get sales for the current year."""
    first_day_of_year = now().replace(month=1, day=1)
    return Order.objects.filter(created_at__date__gte=first_day_of_year, status="Delivered", payment_status=True).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

def daily_sales_view(request):
    """Display detailed daily sales report."""
    today = now().date()
    sales = Order.objects.filter(created_at__date=today, status="Delivered", payment_status=True)
    total = get_daily_sales()
    return render(request, "sales/daily_sales.html", {"sales": sales, "total": total})

def weekly_sales_view(request):
    """Display detailed weekly sales report."""
    last_week = now().date() - timedelta(days=7)
    sales = Order.objects.filter(created_at__date__gte=last_week, status="Delivered", payment_status=True)
    total = get_weekly_sales()
    return render(request, "sales/weekly_sales.html", {"sales": sales, "total": total})

def monthly_sales_view(request):
    """Display detailed monthly sales report."""
    first_day_of_month = now().replace(day=1)
    sales = Order.objects.filter(created_at__date__gte=first_day_of_month, status="Delivered", payment_status=True)
    total = get_monthly_sales()
    return render(request, "sales/monthly_sales.html", {"sales": sales, "total": total})

def yearly_sales_view(request):
    """Display detailed yearly sales report."""
    first_day_of_year = now().replace(month=1, day=1)
    sales = Order.objects.filter(created_at__date__gte=first_day_of_year, status="Delivered", payment_status=True)
    total = get_yearly_sales()
    return render(request, "sales/yearly_sales.html", {"sales": sales, "total": total})

from django.utils.timezone import now, timedelta
def export_orders_csv(request):
    """Exports all order data to a CSV file."""
    orders = Order.objects.values()
    df = pd.DataFrame(orders)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="orders_report.csv"'
    df.to_csv(path_or_buf=response, index=False)
    return response


def export_orders_excel(request):
    """Export all orders as an Excel file."""
    orders = Order.objects.all().values(
        "id", "customer_name", "created_at", "email", "address",
        "total_amount", "status", "delivered_at", "payment_status"
    )

    orders_list = list(orders)

    # Convert timezone-aware datetime fields to naive
    for order in orders_list:
        if order["created_at"]:
            order["created_at"] = make_naive(order["created_at"])
        if order["delivered_at"]:
            order["delivered_at"] = make_naive(order["delivered_at"])

    df = pd.DataFrame(orders_list)

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="orders.xlsx"'

    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    return response


@login_required
def generate_invoice(request, order_id):
    """Generates a PDF invoice for an order."""
    # Get the order object based on the order_id
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Prepare the response as a PDF file
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_{order_id}.pdf"'

    # Create a canvas for the PDF
    p = canvas.Canvas(response)
    p.setFont("Helvetica", 12)

    # Write invoice details
    p.drawString(100, 800, f"Invoice for Order #{order.id}")
    p.drawString(100, 780, f"Customer: {order.customer_name}")
    p.drawString(100, 760, f"Email: {order.email}")
    p.drawString(100, 740, f"Address: {order.address}")
    p.drawString(100, 720, f"Total Amount: Ksh{order.total_amount}")
    p.drawString(100, 700, f"Order Status: {order.status}")
    p.drawString(100, 680, f"Payment Status: {'Paid' if order.payment_status else 'Pending'}")

    # Add the delivery date if available
    if order.status == 'Delivered':
        p.drawString(100, 660, f"Delivery Date: {order.delivered_at.strftime('%B %d, %Y')}")

    # Write items in the order
    y_position = 640
    p.drawString(100, y_position, "Items:")
    y_position -= 20
    for item in order.cart.cart_items.all():
        p.drawString(100, y_position, f"Product: {item.product.name} | Quantity: {item.quantity} | Price: Ksh{item.product.price} | Total: Ksh{item.quantity * item.product.price}")
        y_position -= 20

    # Total amount for the order
    p.drawString(100, y_position, f"Order Total: Ksh{order.total_amount}")

    # Save the PDF
    p.showPage()
    p.save()

    return response


def order_report(request):
    """Generate an order report summary and display it in the template."""

    # **Key Order Metrics**
    total_orders = Order.objects.count()

    # **Fix Revenue Aggregation Query (Only Paid Orders)**
    total_revenue = Order.objects.filter(status="Delivered", payment_status=True).aggregate(
        total_revenue=Sum("total_amount")
    )["total_revenue"] or 0

    # **Fix Order Status Counts**
    pending_orders = Order.objects.filter(status="Pending").count()
    processing_orders = Order.objects.filter(status="Processing").count()
    completed_orders = Order.objects.filter(status="Delivered").count()
    canceled_orders = Order.objects.filter(status="Canceled").count()

    # **Recent Orders Sorted by Date**
    orders = Order.objects.select_related("user").only(
        "id", "created_at", "status", "user__username", "total_amount"
    ).order_by("-created_at")

    # **Prepare Data for the Template**
    context = {
        "total_orders": total_orders,
        "total_revenue": f"KSh {total_revenue:,.2f}",  # Format as Kenyan Shillings
        "pending_orders": pending_orders,
        "processing_orders": processing_orders,
        "completed_orders": completed_orders,
        "canceled_orders": canceled_orders,
        "orders": orders,
    }

    return render(request, "sales/order_report.html", context)



def generate_order_report_pdf(request):
    """Generate a PDF order report using xhtml2pdf."""

    # Get order report data
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(status="Paid").aggregate(
        total_revenue=Sum("total_amount")
    )["total_revenue"] or 0  # ✅ Corrected aggregation

    pending_orders = Order.objects.filter(status="Pending").count()
    processing_orders = Order.objects.filter(status="Processing").count()
    completed_orders = Order.objects.filter(status="Completed").count()
    canceled_orders = Order.objects.filter(status="Canceled").count()

    context = {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "pending_orders": pending_orders,
        "processing_orders": processing_orders,
        "completed_orders": completed_orders,
        "canceled_orders": canceled_orders,
        "orders": Order.objects.all().order_by("-created_at"),
    }

    template = get_template("sales/order_report_pdf.html")
    html = template.render(context)

    # Generate PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="Order_Report.pdf"'
        return response

    return HttpResponse("Error generating PDF", status=500)




def sales_report(request):
    # ✅ Total Sales Revenue & Orders
    total_sales = Order.total_sales() or 0
    total_orders = Order.total_orders() or 0

    # ✅ Top Selling Products
    sales_per_product = Order.sales_per_product()
    product_names = [item["product_name"] for item in sales_per_product]
    product_sales = [item["total_sold"] for item in sales_per_product]

    # ✅ Top Customers
    sales_per_customer = Order.sales_per_customer()
    customer_names = [item["customer"] for item in sales_per_customer]
    customer_spent = [item["total_spent"] for item in sales_per_customer]

    # ✅ Revenue Over Time
    revenue_per_day = (
        Order.objects.filter(status="Delivered", payment_status=True)
        .values(date=F("created_at__date"))  # Use alias for clarity
        .annotate(total_sales=Sum("total_amount"))
        .order_by("date")
    )
    revenue_dates = [entry["date"].strftime("%Y-%m-%d") for entry in revenue_per_day]
    revenue_values = [entry["total_sales"] for entry in revenue_per_day]

    # ✅ Payment Methods Breakdown
    payment_methods = Payment.objects.values("payment_method").annotate(total_count=Count("id"))
    payment_labels = [item["payment_method"] for item in payment_methods]
    payment_counts = [item["total_count"] for item in payment_methods]

    # ✅ Order Status Breakdown
    order_status_counts = Order.objects.values("status").annotate(count=Count("id"))
    order_status_labels = [entry["status"] for entry in order_status_counts]
    order_status_values = [entry["count"] for entry in order_status_counts]

    # ✅ Debugging: Print if Data is Empty
    if not sales_per_product:
        print("⚠️ No sales data found for products!")
    if not sales_per_customer:
        print("⚠️ No sales data found for customers!")
    if not revenue_per_day:
        print("⚠️ No revenue data found over time!")

    context = {
        "total_sales": total_sales,
        "total_orders": total_orders,
        "sales_per_product": product_names,
        "sales_per_product_values": product_sales,
        "sales_per_customer": customer_names,
        "sales_per_customer_values": customer_spent,
        "revenue_per_day_dates": revenue_dates,
        "revenue_per_day_values": revenue_values,
        "payment_methods_labels": payment_labels,
        "payment_methods_values": payment_counts,
        "order_status_labels": order_status_labels,
        "order_status_values": order_status_values,
    }

    return render(request, "analytics/sales_report.html", context)