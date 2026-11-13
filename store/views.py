import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.conf import settings
from django.contrib.auth.models import User

from .models import Product, Order, OrderItem
from .forms import ProductForm

# ==========================================
# 1. STOREFRONT VIEWS
# ==========================================

def shop(request):
    query = request.GET.get('q')
    category = request.GET.get('category')
    products = Product.objects.all()
    
    if query: 
        products = products.filter(name__icontains=query)
    if category: 
        products = products.filter(category__iexact=category)
        
    categories = [c for c in Product.objects.values_list('category', flat=True).distinct() if c]
    
    return render(request, 'store/shop.html', {
        'products': products, 
        'categories': categories, 
        'query': query, 
        'selected_category': category
    })

def category_view(request, category_name):
    products = Product.objects.filter(category__iexact=category_name)
    return render(request, 'store/category.html', {
        'products': products, 
        'category_name': category_name
    })

# ==========================================
# 2. CART VIEWS
# ==========================================

def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    messages.success(request, "Item added to cart!")
    return redirect('shop')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart: 
        del cart[str(product_id)]
    request.session['cart'] = cart
    return redirect('cart_detail')

def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        item_total = product.price * quantity
        total_price += item_total
        cart_items.append({'product': product, 'quantity': quantity, 'total': item_total})
    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total_price': total_price})

# ==========================================
# 3. CHECKOUT & UPI PAYMENT VIEWS
# ==========================================

import urllib.parse
from django.conf import settings
from django.core.mail import EmailMessage

def checkout(request):
    cart = request.session.get('cart', {})
    if not cart: return redirect('shop')

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            first_name=request.POST.get('first_name'), 
            last_name=request.POST.get('last_name'), 
            email=request.POST.get('email'), 
            address=request.POST.get('address'),
            payment_method=payment_method,
            is_paid=False # ALWAYS False initially for manual UPI
        )

        total_price = 0
        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, id=product_id)
            OrderItem.objects.create(order=order, product=product, price=product.price, quantity=quantity)
            total_price += product.price * quantity
        
        order.total_price = total_price
        order.save()
        request.session['cart'] = {} 

        if payment_method == 'UPI':
            # Generate UPI URL and QR Code
            upi_url = f"upi://pay?pa={settings.UPI_ID}&pn={urllib.parse.quote(settings.UPI_NAME)}&am={total_price}&cu=INR&tn=Order_{order.id}"
            qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_url)}"
            
            return render(request, 'store/upi_payment.html', {
                'order': order, 
                'upi_id': settings.UPI_ID, 
                'qr_code_url': qr_code_url,
                'total_price': total_price
            })
            
        # For Cash on Delivery, it's also pending until delivery
        return render(request, 'store/pending.html', {'order': order})

    return render(request, 'store/checkout.html')

# ==========================================
# 4. USER AUTHENTICATION VIEWS
# ==========================================

from django import forms

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('shop')
    else:
        form = UserCreationForm()
        # Add CSS classes to the default form fields
        form.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Choose a username'})
        form.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Create a password'})
        form.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})
        
    return render(request, 'store/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('shop')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'store/login.html')

def user_logout(request):
    logout(request)
    return redirect('shop')

# ==========================================
# 5. ADMIN DASHBOARD & INVENTORY VIEWS
# ==========================================

@staff_member_required
def dashboard(request):
    total_revenue = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_orders = Order.objects.count()
    total_customers = User.objects.filter(is_staff=False).count()
    total_products = Product.objects.count()
    
    recent_orders = Order.objects.order_by('-created_at')[:10]

    return render(request, 'store/dashboard.html', {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_products': total_products,
        'recent_orders': recent_orders,
    })

@staff_member_required
def manage_products(request):
    products = Product.objects.all().order_by('-id')
    return render(request, 'store/manage_products.html', {'products': products})

@staff_member_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('manage_products')
    else:
        form = ProductForm()
    return render(request, 'store/product_form.html', {'form': form, 'title': 'Add New Product'})

@staff_member_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('manage_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'store/product_form.html', {'form': form, 'title': 'Edit Product'})

@staff_member_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('manage_products')

@staff_member_required
def manage_customers(request):
    customers = User.objects.filter(is_staff=False).order_by('-date_joined')
    return render(request, 'store/manage_customers.html', {'customers': customers})

def pending_page(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/pending.html', {'order': order})

@staff_member_required
def manage_orders(request):
    # Get all orders that are NOT paid yet
    pending_orders = Order.objects.filter(is_paid=False).order_by('-created_at')
    paid_orders = Order.objects.filter(is_paid=True).order_by('-created_at')[:10]
    return render(request, 'store/manage_orders.html', {
        'pending_orders': pending_orders,
        'paid_orders': paid_orders
    })

@staff_member_required
def confirm_payment_and_send_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # 1. Mark as paid
    order.is_paid = True
    order.save()

    # 2. Send the Invoice Email
    subject = f"Payment Confirmed - Invoice for Order #{order.id}"
    body = f"""
    Hi {order.first_name},
    
    We have received your payment of ₹{order.total_price}. Your order is now confirmed!
    
    Order Details:
    Order ID: #{order.id}
    Payment Method: {order.payment_method}
    
    We will ship your items shortly.
    
    Thank you for shopping with Mini Mart!
    """
    
    email = EmailMessage(
        subject,
        body,
        'your_email@gmail.com', # Replace with your email
        [order.email],          # Sends to the customer
    )
    email.send()

    messages.success(request, f"Invoice sent to {order.email}!")
    return redirect('manage_orders')
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # If it's Cash on Delivery, we can assume the order is confirmed
    if order.payment_method == 'Cash on Delivery':
        order.is_paid = True
        order.save()
        
    # If it's UPI, redirect them to the pending page (since they need to wait for you to verify it)
    if order.payment_method == 'UPI':
        return redirect('pending_page', order_id=order.id)

    # Show the invoice for COD
    return render(request, 'store/success.html', {'order': order})