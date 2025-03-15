from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Cart, CartItem, Order
from inventory.models import Product
from .forms import *
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
                return redirect('order:payment', order_id=order.id)

    else:
        form = OrderForm()

    return render(request, 'cart/checkout.html', {'form': form})

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'cart/order_summary.html', {'order': order})

@login_required
def payment_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        # Simulate payment success (Stripe, PayPal, etc.)
        order.payment_status = "Paid"
        order.save()

        messages.success(request, "💳 Payment successful! Your order is confirmed.")
        return redirect('order:order_confirmation', order_id=order.id)

    return render(request, 'cart/payment.html', {'order': order})

##payment managemet Admin
@login_required
@user_passes_test(is_admin)
def manage_payments(request):
    """Admin View: Display all payments."""
    payments = Payment.objects.all().order_by('-payment_date')
    return render(request, 'admin_payment/manage_payments.html', {'payments': payments})

@login_required
@user_passes_test(is_admin)
def payment_details(request, payment_id):
    """Admin View: Display payment details."""
    payment = get_object_or_404(Payment, id=payment_id)
    return render(request, 'admin_payment/payment_details.html', {'payment': payment})

@login_required
@user_passes_test(is_admin)
def issue_refund(request, payment_id):
    """Admin View: Process refunds."""
    payment = get_object_or_404(Payment, id=payment_id)

    if payment.issue_refund():
        messages.success(request, f"Refund issued for Order {payment.order.id}.")
    else:
        messages.error(request, "Refund failed or already issued.")

    return redirect('manage_payments')

###customer payment
@login_required
def customer_payments(request):
    """Customer View: Display payments made by logged-in user."""
    payments = Payment.objects.filter(user=request.user).order_by('-payment_date')
    return render(request, 'customer_payment/customer_payments.html', {'payments': payments})

@login_required
def request_refund(request, payment_id):
    """Customer View: Allow users to request a refund."""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    if payment.payment_status == "Successful" and not payment.refund_status:
        payment.payment_status = "Pending Refund"
        payment.save()
        messages.success(request, "Your refund request has been submitted.")
    else:
        messages.error(request, "Refund request failed. Payment is either not successful or already refunded.")

    return redirect('customer_payments')


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')  # Show latest orders first
    return render(request, 'cart/my_orders.html', {'orders': orders})

##order managemnt
@staff_member_required
def admin_order_list(request):
    """Displays all orders in the admin dashboard."""
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'admin/admin_order_list.html', {'orders': orders})

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

        return redirect('order:admin_order_detail', order_id=order.id)

    return render(request, 'admin/update_order_status.html', {'order': order, 'status_choices': Order.STATUS_CHOICES})

@staff_member_required
def delete_order(request, order_id):
    """Allows admin to delete an order."""
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        order.delete()
        messages.success(request, f"🗑️ Order {order.id} has been deleted successfully.")
        return redirect('order:admin_order_list')

    return render(request, 'admin/delete_order.html', {'order': order})