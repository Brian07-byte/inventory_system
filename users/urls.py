from django.urls import path
from . import views
from django.shortcuts import render, redirect
from .views import signup_view, login_view,logout_view
from .views import customer_dashboard, admin_dashboard, dashboard_redirect,user_profile

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path("profile/", user_profile, name="user_profile"),
##dashboard redirections
    path('dashboard/', dashboard_redirect, name='dashboard_redirect'),
    path('dashboard/customer/', customer_dashboard, name='customer_dashboard'),
    path('dashboard/admin/', admin_dashboard, name='admin_dashboard'),

    # Placeholder views
    path('admin/manage-inventory/', lambda request: render(request, 'admin/manage_inventory.html'), name='manage_inventory'),
    path('admin/manage-orders/', lambda request: render(request, 'admin/manage_orders.html'), name='manage_orders'),
    path('admin/manage-users/', lambda request: render(request, 'admin/manage_users.html'), name='manage_users'),
    path('admin/view-reports/', lambda request: render(request, 'admin/view_reports.html'), name='view_reports'),

    path('customer/browse-products/', lambda request: render(request, 'customer/browse_products.html'), name='browse_products'),
    path('customer/view-cart/', lambda request: render(request, 'customer/view_cart.html'), name='view_cart'),
    path('customer/track-orders/', lambda request: render(request, 'customer/track_orders.html'), name='track_orders'),
    path('customer/profile/', lambda request: render(request, 'customer/profile.html'), name='profile'),
    
     # User Management (Admin Only)
    path('admin/manage-users/', views.manage_users, name='manage_users'),
    path('admin/change-role/<int:user_id>/<str:new_role>/', views.change_user_role, name='change_user_role'),
    path('admin/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
]
