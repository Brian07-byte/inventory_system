from django.urls import path
from . import views

urlpatterns = [
    # API Endpoints (return JSON)
    path('api/sales/', views.sales_report_api, name='sales_report_api'),
    path('api/stock/', views.stock_report_api, name='stock_report_api'),
    path('api/users/', views.user_report_api, name='user_report_api'),
    path('api/payments/', views.payment_report_api, name='payment_report_api'),

    # Web Page Reports (render HTML)
    path('sales/', views.sales_report_page, name='sales_report_page'),
    path('stock/', views.stock_report_page, name='stock_report_page'),
    path('users/', views.user_report_page, name='user_report_page'),
    path('payments/', views.payment_report_page, name='payment_report_page'),
    path('products/', views.product_report_page, name='product_report_page'),
]
