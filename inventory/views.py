from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum
from xhtml2pdf import pisa
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.http import JsonResponse
from .models import Sale, Product, Supplier, Category, Stock
from .forms import ProductForm, CategoryForm, SupplierForm, StockForm, SalesReportForm
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import csv

# ✅ View all products
def view_products(request):
    products = Product.objects.all()
    return render(request, "inventory/view_products.html", {"products": products})


# ✅ Add a new product
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            
            # Ensure a stock entry exists
            if not Stock.objects.filter(product=product).exists():
                Stock.objects.create(product=product, quantity=0)
            
            messages.success(request, f"✅ {product.name} added successfully!")
            return redirect("inventory:view_products")
        else:
            messages.error(request, "❌ Error adding product. Please check the form.")
    else:
        form = ProductForm()

    return render(request, "inventory/add_product.html", {"form": form})


# ✅ Edit a product
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"✏️ {product.name} updated successfully!")
            return redirect('inventory:view_products')
        else:
            messages.error(request, "❌ Error updating product. Please check the form.")
    else:
        form = ProductForm(instance=product)

    return render(request, "inventory/edit_product.html", {"form": form, "product": product})


# ✅ Delete a product
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    total_stock = product.get_available_stock()

    if total_stock > 0:
        messages.error(request, f"❌ Cannot delete '{product.name}'! It still has {total_stock} in stock.")
        return redirect("inventory:view_products")

    if request.method == "POST":
        product.stock_entries.all().delete()
        product.delete()
        messages.success(request, f"🗑️ '{product.name}' deleted successfully!")
        return redirect("inventory:view_products")

    return render(request, "inventory/confirm_delete.html", {"product": product})


# ✅ View all categories
def view_categories(request):
    categories = Category.objects.all()
    return render(request, "inventory/view_categories.html", {"categories": categories})


# ✅ Add a new category
def add_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"📁 Category '{category.name}' added successfully!")
            return redirect("inventory:view_categories")
        else:
            messages.error(request, "❌ Error adding category.")
    else:
        form = CategoryForm()

    return render(request, "inventory/add_category.html", {"form": form})


# ✅ View all suppliers with search functionality
def supplier_list(request):
    query = request.GET.get('q')
    suppliers = Supplier.objects.filter(name__icontains=query) if query else Supplier.objects.all()

    return render(request, 'supplier/supplier_list.html', {'suppliers': suppliers, 'query': query})


# ✅ Add a new supplier
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Supplier added successfully! ✅")
            return redirect('inventory:supplier_list')
        else:
            messages.error(request, "Error adding supplier. ❌")
    else:
        form = SupplierForm()
    return render(request, 'supplier/supplier_form.html', {'form': form, 'title': 'Add Supplier'})


# ✅ Update an existing supplier
def supplier_update(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('inventory:supplier_list')
    else:
        form = SupplierForm(instance=supplier)

    return render(request, 'supplier/supplier_form.html', {'form': form, 'supplier': supplier})


# ✅ Delete a supplier
def supplier_delete(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    if request.method == 'POST':
        supplier.delete()
        return redirect('inventory:supplier_list')
    return render(request, 'supplier/supplier_delete.html', {'supplier': supplier})


# ✅ View stock levels
def view_stock(request):
    stock_entries = Stock.objects.all()
    return render(request, "inventory/stock_list.html", {"stock_entries": stock_entries})


# ✅ Update stock levels (increase or decrease)
@csrf_exempt
def update_stock(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    stock_entry = Stock.objects.filter(product=product).first()

    if request.method == "POST":
        action = request.POST.get("action")
        quantity = int(request.POST.get("quantity", 0))

        if stock_entry:
            try:
                if action == "add":
                    stock_entry.update_stock(quantity)
                    messages.success(request, f"Stock updated successfully! ✅")
                elif action == "reduce":
                    stock_entry.reduce_stock(quantity)
                    messages.success(request, f"Stock reduced successfully! ✅")
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "No stock entry found for this product.")

        return redirect("inventory:update_stock", product_id=product.id)

    return render(request, "inventory/update_stock_list.html", {"product": product, "stock": stock_entry})


# ✅ API endpoint to check stock level
def check_stock(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    stock_entry = Stock.objects.filter(product=product).first()

    if stock_entry:
        return JsonResponse({"product": product.name, "available_stock": stock_entry.quantity})
    else:
        return JsonResponse({"error": "Stock entry not found"}, status=404)


# ✅ Search products
def search_products(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()

    products = Product.objects.all()
    if query:
        products = products.filter(name__icontains=query)
    if category_id:
        products = products.filter(category_id=category_id)

    if not products.exists():
        messages.warning(request, f"No results found for '{query}'.")

    categories = Category.objects.all()

    return render(request, 'inventory/search_results.html', {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category_id
    })


# ✅ Customer product browsing
def product_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')

    products = Product.objects.all()
    
    if query:
        products = products.filter(name__icontains=query)  
    
    if category_id:
        products = products.filter(category_id=category_id)  

    categories = Category.objects.all()

    return render(request, 'inventory/customer/browse_products.html', {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category_id
    })


# ✅ Product details for customers
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'inventory/customer/product_detail.html', {'product': product})

