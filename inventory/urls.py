from django.urls import path
from .views import *
from . import views
app_name = 'inventory'

urlpatterns = [
    path('products/', views.view_products, name='view_products'),
    path('products/add/', add_product, name='add_product'),
    path('products/edit/<int:product_id>/', edit_product, name='edit_product'),
    path('products/delete/<int:product_id>/', delete_product, name='delete_product'),
    path('products/search/', search_products, name='search_products'),
    path('stock/', view_stock, name='view_stock'),
    path('stock/update/', update_stock_list, name='update_stock_list'),
    path('stock/update/<int:product_id>/', update_stock, name='update_stock'),

    # Supplier
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/edit/<int:id>/', views.supplier_update, name='supplier_update'),
    path('suppliers/delete/<int:id>/', views.supplier_delete, name='supplier_delete'),

    # Customer
    path('browse-products/', product_list, name="browse_products"),
    path('products/<int:product_id>/', product_detail, name='product_detail'),
]
