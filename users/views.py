from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import *
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
    return render(request, 'customer/dashboard.html')

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get total counts
    total_users = CustomUser.objects.count()
    total_orders = Order.objects.count()
    total_products = Product.objects.count()

    # Calculate total revenue
    total_revenue = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0

    # Get recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:5]

    # Get recent notifications (optional)

    # Revenue per month - Use the correct field for date, such as `payment_date`
    revenue_per_month = Payment.objects.filter(payment_date__gte=timezone.now().replace(month=1, day=1)) \
        .values('payment_date__month') \
        .annotate(total_revenue=Sum('amount')) \
        .order_by('payment_date__month')

    # Orders per month
    orders_per_month = Order.objects.filter(created_at__gte=timezone.now().replace(month=1, day=1)) \
        .values('created_at__month') \
        .annotate(order_count=Sum('id')) \
        .order_by('created_at__month')

    # Product category distribution
    product_categories = Product.objects.values('category__name').annotate(category_count=Sum('id'))

    # Prepare data for charts
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    monthly_revenue = [0] * 12
    for record in revenue_per_month:
        month_index = record['payment_date__month'] - 1
        monthly_revenue[month_index] = record['total_revenue']

    monthly_orders = [0] * 12
    for record in orders_per_month:
        month_index = record['created_at__month'] - 1
        monthly_orders[month_index] = record['order_count']

    category_data = {category['category__name']: category['category_count'] for category in product_categories}

    context = {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'monthly_revenue': monthly_revenue,
        'monthly_orders': monthly_orders,
        'category_data': category_data,
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
