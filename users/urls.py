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
    # User views
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
]
