from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from reports.models import *
from django.contrib.auth.models import User
from orders.models import Order
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

# Admin Dashboard
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    return render(request, "admin/dashboard.html")


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
