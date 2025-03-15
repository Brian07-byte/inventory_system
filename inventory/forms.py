from django import forms
from .models import Product, Supplier, Category, Stock

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter category name"}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_number', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Supplier Name'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Contact Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email Address'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter Supplier Address'}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'category', 'supplier', 'description', 'price', 'image']


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = "__all__"
        widgets = {
            "product": forms.Select(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Enter stock quantity"}),
        }
    labels = {
        "product": "Select Product",
        "quantity": "Stock Quantity",
    }
