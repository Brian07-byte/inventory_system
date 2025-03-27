from django import forms
from django.contrib.auth import get_user_model
from .models import Product, Supplier, Category, Stock, Sale

User = get_user_model()  # Use the default user model

# ===========================
# CATEGORY FORM
# ===========================
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter category name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter category description"}),
        }
        labels = {
            "name": "Category Name",
            "description": "Category Description",
        }


# ===========================
# SUPPLIER FORM
# ===========================
class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'supplier_code', 'contact_number', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Supplier Name'}),
            'supplier_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Unique Supplier Code'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Contact Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email Address'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter Supplier Address'}),
        }

    def clean_supplier_code(self):
        supplier_code = self.cleaned_data.get('supplier_code')
        if Supplier.objects.filter(supplier_code=supplier_code).exists():
            raise forms.ValidationError("A supplier with this code already exists. Please enter a unique code.")
        return supplier_code

# ===========================
# PRODUCT FORM
# ===========================
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'category', 'supplier', 'description', 'price', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Product Name'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter SKU'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter Product Description'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Price'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            "name": "Product Name",
            "sku": "SKU",
            "category": "Category",
            "supplier": "Supplier",
            "description": "Description",
            "price": "Price (in $)",
            "image": "Product Image",
        }


# ===========================
# STOCK FORM
# ===========================
class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['product', 'quantity', 'low_stock_threshold']
        widgets = {
            "product": forms.Select(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Enter stock quantity"}),
            "low_stock_threshold": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Enter low stock threshold"}),
        }
        labels = {
            "product": "Select Product",
            "quantity": "Stock Quantity",
            "low_stock_threshold": "Low Stock Threshold",
        }


# ===========================
# SALES REPORT FORM
# ===========================
class SalesReportForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Start Date"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="End Date"
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Product"
    )
    customer = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Customer"
    )
