from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import *
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, F
from django.utils import timezone
from .models import CustomUser
from django.utils import timezone
from datetime import datetime
from collections import defaultdict
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from orders.models import *
from inventory.models import *
from django.contrib.auth import get_user_model

from .forms import UserRegistrationForm

User = get_user_model()

# Check if user is an admin
def is_admin(user):
    return user.is_authenticated and user.is_staff

# User Signup
def signup_view(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Signup successful! Welcome.")
            return redirect("home")
        else:
            messages.error(request, "Please correct the errors below.")

    form = UserRegistrationForm()
    return render(request, "users/signup.html", {"form": form})

# User Login
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard_redirect')  # Redirect to the right dashboard
        else:
            return render(request, 'users/login.html', {'error': 'Invalid credentials'})

    return render(request, 'users/login.html')

# User Logout
def logout_view(request):
    logout(request)
    return redirect('home')  # Redirect to home after logout

# Redirect users to their respective dashboards
@login_required
def dashboard_redirect(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    return redirect('customer_dashboard')

# Customer Dashboard
@login_required
def customer_dashboard(request):
    """Customer Dashboard - Displays user-specific order statistics and history"""

    user = request.user  # Get logged-in user

    # **Key Metrics**
    total_orders = Order.objects.filter(user=user).count()
    total_spent = Order.objects.filter(user=user, payment_status=True).aggregate(
        total_spent=Sum('total_amount')
    )['total_spent'] or 0

    # **Recent Orders (Latest 5)**
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]

    # **Orders per Month (for charts)**
    current_year = now().year
    orders_per_month = Order.objects.filter(user=user, created_at__year=current_year) \
        .values_list('created_at__month') \
        .annotate(order_count=Count('id')) \
        .order_by('created_at__month')

    # **Spending per Month (for charts)**
    spending_per_month = Order.objects.filter(user=user, payment_status=True, created_at__year=current_year) \
        .values_list('created_at__month') \
        .annotate(total_spent=Sum('total_amount')) \
        .order_by('created_at__month')

    # **Format Data for Charts**
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_orders = [0] * 12
    monthly_spending = [0] * 12

    for month, order_count in orders_per_month:
        monthly_orders[month - 1] = order_count

    for month, spent in spending_per_month:
        monthly_spending[month - 1] = spent

    # **Context Data**
    context = {
        'total_orders': total_orders,
        'total_spent': f"KSh {total_spent:,.2f}",  # Currency formatting
        'recent_orders': recent_orders,
        'monthly_orders': monthly_orders,
        'monthly_spending': monthly_spending,
        'months': months,
    }

    return render(request, 'customer/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # **Key Metrics**
    total_users = CustomUser.objects.count()
    total_orders = Order.total_orders()  # Count of delivered orders
    total_products = Product.objects.count()
    total_revenue = Order.total_revenue()  # Revenue from delivered and paid orders
    total_inventory_stock = Stock.objects.aggregate(total=Sum('quantity'))['total'] or 0
    low_stock_products = Stock.objects.filter(quantity__lt=10).count()
    total_suppliers = Supplier.objects.count()
    total_customers = CustomUser.objects.filter(is_staff=False).count()  # Counting non-admin users as customers

    # **Recent Data**
    recent_orders = Order.objects.select_related('user').only(
        'id', 'created_at', 'status', 'user__username', 'total_amount'
    ).order_by('-created_at')[:5]

    recent_inventory_updates = Stock.objects.select_related('product').only(
        'id', 'product__name', 'quantity', 'last_updated'
    ).order_by('-last_updated')[:5]

    # **Monthly Revenue (for charts)**
    current_year = timezone.now().year
    revenue_per_month = Order.objects.filter(status="Delivered", payment_status=True, created_at__year=current_year) \
        .values_list('created_at__month') \
        .annotate(total_revenue=Sum('total_amount')) \
        .order_by('created_at__month')

    # **Orders Per Month (count only delivered orders)**
    orders_per_month = Order.objects.filter(status="Delivered", created_at__year=current_year) \
        .values_list('created_at__month') \
        .annotate(order_count=Count('id')) \
        .order_by('created_at__month')

    # **Sales Per Product**
    product_sales = Order.sales_per_product()

    # **Sales Per Customer**
    customer_sales = Order.sales_per_customer()

    # **Product Categories**
    product_categories = Product.objects.values('category__name') \
        .annotate(category_count=Count('id')) \
        .order_by('-category_count')

    # **Format Data for Charts**
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_revenue = [0] * 12
    monthly_orders = [0] * 12
    category_data = {category['category__name']: category['category_count'] for category in product_categories}

    for month, revenue in revenue_per_month:
        monthly_revenue[month - 1] = revenue

    for month, order_count in orders_per_month:
        monthly_orders[month - 1] = order_count

    # **Context Data**
    context = {
        'total_users': total_users,
        'total_customers': total_customers,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_revenue': f"Ksh{total_revenue:,.2f}",  # Formatting as currency
        'total_inventory_stock': total_inventory_stock,
        'low_stock_products': low_stock_products,
        'total_suppliers': total_suppliers,
        'recent_orders': recent_orders,
        'recent_inventory_updates': recent_inventory_updates,
        'monthly_revenue': monthly_revenue,
        'monthly_orders': monthly_orders,
        'category_data': category_data,
        'months': months,
        'product_sales': product_sales,
        'customer_sales': customer_sales,
    }

    return render(request, "admin/dashboard.html", context)
# User Profile View
@login_required
def user_profile(request):
    """View for customers to update their profile."""
    return render(request, "user/profile.html", {"user": request.user})

# --- ADMIN USER MANAGEMENT ---
@login_required
@user_passes_test(is_admin)
def manage_users(request):
    """View for admin to see all users."""
    users = User.objects.all()
    return render(request, "admin/manage_users.html", {"users": users})

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    """Allows admin to delete users."""
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, "User deleted successfully.")
    return redirect("manage_users")

@login_required
@user_passes_test(is_admin)
def change_user_role(request, user_id, new_role):
    """Allows admin to change user roles (customer/admin)."""
    user = get_object_or_404(User, id=user_id)
    user.role = new_role
    user.save()
    messages.success(request, f"User role updated to {new_role}.")
    return redirect("manage_users")



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import CustomUser
from .forms import CustomUserForm

# List all users (Admin only)
class UserListView(ListView):
    model = CustomUser
    template_name = 'user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        # Only allow admins to view the user list
        if self.request.user.is_admin():
            return CustomUser.objects.all()
        else:
            messages.error(self.request, "You do not have permission to view the users list.")
            return CustomUser.objects.none()

# Create a new user (Admin only)
class UserCreateView(CreateView):
    model = CustomUser
    form_class = CustomUserForm
    template_name = 'user_form.html'
    success_url = reverse_lazy('user_list')

    def form_valid(self, form):
        messages.success(self.request, "User created successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error creating user. Please check the form.")
        return super().form_invalid(form)

# Update user details (Admin or the user themselves)
class UserUpdateView(UpdateView):
    model = CustomUser
    form_class = CustomUserForm
    template_name = 'user_form.html'
    success_url = reverse_lazy('user_list')

    def form_valid(self, form):
        messages.success(self.request, "User updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error updating user. Please check the form.")
        return super().form_invalid(form)

# Delete a user (Admin only)
class UserDeleteView(DeleteView):
    model = CustomUser
    template_name = 'user_confirm_delete.html'
    success_url = reverse_lazy('user_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "User deleted successfully.")
        return super().delete(request, *args, **kwargs)
