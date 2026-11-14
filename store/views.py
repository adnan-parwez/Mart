import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.conf import settings
from .models import Product, Order, OrderItem, CustomUser
from django.core.mail import EmailMultiAlternatives # <-- Put it here!
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from .models import Product, Order, OrderItem, CustomUser, Address, Coupon
from .forms import ProductForm, CustomUserCreationForm
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
    
    product = get_object_or_404(Product, id=product_id)
    # THIS IS THE EXACT TEXT THAT WILL POPUP
    messages.success(request, f"1 item ({product.name}) has been added to cart!")
    
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
    subtotal = 0
    
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        item_total = product.price * quantity
        subtotal += item_total
        cart_items.append({'product': product, 'quantity': quantity, 'total': item_total})
        
    coupon_id = request.session.get('coupon_id')
    coupon_error = request.session.pop('coupon_error', None) # 👈 GET AND CLEAR ERROR
    discount_amount = 0
    total_price = subtotal
    
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, active=True)
            if coupon.discount_type == 'percentage':
                discount_amount = (subtotal * coupon.discount_value) / 100
            else:
                discount_amount = coupon.discount_value
            if discount_amount > subtotal:
                discount_amount = subtotal
            total_price = subtotal - discount_amount
        except Coupon.DoesNotExist:
            del request.session['coupon_id']

    delivery_fee = 0 if total_price >= 500 else 10
    final_total = total_price + delivery_fee

    return render(request, 'store/cart.html', {
        'cart_items': cart_items, 
        'subtotal': subtotal,
        'total_price': final_total,
        'discount_amount': discount_amount,
        'delivery_fee': delivery_fee,
        'coupon_error': coupon_error # 👈 PASS TO TEMPLATE
    })
# ==========================================
# 3. CHECKOUT & UPI PAYMENT VIEWS
# ==========================================

import urllib.parse
from django.conf import settings
from django.core.mail import EmailMessage

from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from .models import Order, OrderItem, Product, Address, CustomUser
import uuid

def checkout(request):

    if request.user.is_authenticated and request.user.is_staff:
        messages.info(request, "Admins cannot place orders. You are being redirected to the dashboard.")
        return redirect('dashboard')
    
    cart = request.session.get('cart', {})
    if not cart: 
        return redirect('shop')

    # Get saved addresses if the user is logged in
    saved_addresses = []
    if request.user.is_authenticated:
        saved_addresses = Address.objects.filter(user=request.user)

    if request.method == 'POST':
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        delivery_type = request.POST.get('delivery_type')
        address_id = request.POST.get('address_id')
        
        # Determine Address based on type
        if delivery_type == 'store_pickup':
            address_str = "STORE PICKUP: RUMI MART"
            city = "Store Pickup"
            pincode = "000000"
        elif address_id and address_id != 'new':
            # Use saved address
            addr = Address.objects.get(id=address_id)
            address_str = addr.address_line
            city = addr.city
            pincode = addr.pincode
            full_name = addr.full_name
            phone = addr.phone
        else:
            # New address
            address_str = request.POST.get('address')
            city = request.POST.get('city')
            pincode = request.POST.get('pincode')

        # 1. HANDLE GUEST ACCOUNT CREATION
        user = request.user if request.user.is_authenticated else None
        
        if not user:
            # Check if user exists with this email
            user = CustomUser.objects.filter(email=email).first()
            if not user:
                # Create new guest account
                random_password = get_random_string(length=10)
                user = CustomUser.objects.create_user(
                    email=email,
                    password=random_password,
                    first_name=full_name.split(' ')[0],
                    phone=phone
                )
        if not (full_name and phone and email and len(phone) == 10):
            messages.error(request, "Please provide a valid name, 10-digit phone number, and email.")
            return redirect('checkout')
        
        # 2. SAVE ADDRESS TO PROFILE (If they don't have it)
        if delivery_type == 'home' and address_str and user:
            Address.objects.get_or_create(
                user=user,
                address_line=address_str,
                defaults={'full_name': full_name, 'phone': phone, 'city': city, 'pincode': pincode}
            )

        # 3. CREATE ORDER
        order = Order.objects.create(
            user=user,
            first_name=full_name,
            last_name="",
            email=email,
            phone=phone,
            address=address_str,
            city=city,
            pincode=pincode,
            payment_method=request.POST.get('payment_method'),
            is_paid=False
        )

        # 4. MOVE CART TO ORDER
        total_price = 0
        for product_id, quantity in cart.items():
            product = Product.objects.get(id=product_id)
            OrderItem.objects.create(order=order, product=product, price=product.price, quantity=quantity)
            total_price += product.price * quantity
        
        order.total_price = total_price
        order.save()
        request.session['cart'] = {} 

        if request.POST.get('payment_method') == 'UPI':
            # Existing UPI logic...
            pass
            
        return redirect('pending_page', order_id=order.id)

    return render(request, 'store/checkout.html', {'saved_addresses': saved_addresses})

# ==========================================
# 4. USER AUTHENTICATION VIEWS
# ==========================================


from .forms import ProductForm, CustomUserCreationForm # Import the new form

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False) # Don't save yet
            user.first_name = form.cleaned_data['first_name'] # Add First Name
            user.last_name = form.cleaned_data['last_name']   # Add Last Name
            user.save() # Now save to database
            login(request, user)
            messages.success(request, f"Your account has been created as {user.email}")
            return redirect('shop')
        else:
            # If there's an error (like duplicate email), it will print in terminal and show on form
            print(form.errors)
    else:
        form = CustomUserCreationForm()
    return render(request, 'store/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email') # Use .get() to avoid KeyError
        password = request.POST.get('password')
        
        # Authenticate using the email field
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"You are logged in as {user.email}")
            return redirect('shop')
        else:
            messages.error(request, "Invalid email or password.")
            
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
    total_customers = CustomUser.objects.filter(is_staff=False).count() # Updated to CustomUser
    total_products = Product.objects.count()
    
    pending_orders = Order.objects.filter(is_paid=False).order_by('-created_at')
    recent_orders = Order.objects.filter(is_paid=True).order_by('-created_at')[:5]

    return render(request, 'store/dashboard.html', {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_products': total_products,
        'pending_orders': pending_orders,
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
    customers = CustomUser.objects.filter(is_staff=False).order_by('-date_joined')
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
    order.is_paid = True
    order.save()

    # Email logic (assuming settings are correct)
    subject = f"Payment Confirmed - Invoice for Order #{order.id}"
    html_message = render_to_string('store/email_invoice.html', {'order': order})
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject, plain_message, 'adnan.uc3m@gmail.com', [order.email]
    )
    email.attach_alternative(html_message, "text/html")
    email.send()

    messages.success(request, f"Order #{order.id} confirmed & invoice sent!")
    return redirect('dashboard') 

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

def update_cart(request, product_id, action):
    cart = request.session.get('cart', {})
    product_id = str(product_id)
    
    if action == 'increase':
        cart[product_id] = cart.get(product_id, 0) + 1
    elif action == 'decrease':
        cart[product_id] = cart.get(product_id, 0) - 1
        if cart[product_id] <= 0:
            del cart[product_id]
            
    request.session['cart'] = cart
    return redirect('cart_detail')

@login_required(login_url='/login/')
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/my_orders.html', {'orders': orders})

@login_required(login_url='/login/')
def order_invoice(request, order_id):
    # Get the order, but ensure it belongs to the logged-in user
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # If it's not paid, don't let them see the final invoice
    if not order.is_paid:
        messages.warning(request, "Payment is still pending verification.")
        return redirect('my_orders')
        
    return render(request, 'store/invoice.html', {'order': order})

@login_required(login_url='/login/')
def profile(request):
    return render(request, 'store/profile.html')

@login_required(login_url='/login/')
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.phone = request.POST.get('phone')
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')
    return render(request, 'store/edit_profile.html')

@login_required(login_url='/login/')
def add_to_wishlist(request, product_id):
    # Get the current wishlist from the session, or create an empty list
    wishlist = request.session.get('wishlist', [])
    
    if product_id not in wishlist:
        wishlist.append(product_id)
        request.session['wishlist'] = wishlist
        messages.success(request, "Item added to your Wishlist! ❤️")
    else:
        messages.info(request, "Item is already in your Wishlist.")
        
    # Redirect them back to the page they were on
    return redirect(request.META.get('HTTP_REFERER', 'shop'))

@login_required(login_url='/login/')
def wishlist(request):
    wishlist_ids = request.session.get('wishlist', [])
    products = Product.objects.filter(id__in=wishlist_ids)
    return render(request, 'store/wishlist.html', {'products': products})

@staff_member_required
def edit_customer(request, user_id):
    customer = get_object_or_404(CustomUser, id=user_id, is_staff=False)
    
    if request.method == 'POST':
        customer.first_name = request.POST.get('first_name')
        customer.last_name = request.POST.get('last_name')
        customer.email = request.POST.get('email')
        customer.phone = request.POST.get('phone')
        customer.save()
        messages.success(request, "Customer details updated successfully!")
        return redirect('manage_customers')
        
    return render(request, 'store/edit_customer.html', {'customer': customer})

@staff_member_required
def delete_customer(request, user_id):
    customer = get_object_or_404(CustomUser, id=user_id, is_staff=False)
    customer.delete()
    messages.success(request, "Customer removed successfully!")
    return redirect('manage_customers')


def move_to_wishlist(request, product_id):
    # 1. Remove from Cart
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
    request.session['cart'] = cart

    # 2. Add to Wishlist
    wishlist = request.session.get('wishlist', [])
    if product_id not in wishlist:
        wishlist.append(product_id)
        request.session['wishlist'] = wishlist
        
    messages.success(request, "Item moved to your Wishlist! ❤️")
    return redirect('cart_detail')


def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code')
        
        # Calculate subtotal to check minimum order
        cart = request.session.get('cart', {})
        subtotal = 0
        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, id=product_id)
            subtotal += product.price * quantity
            
        try:
            coupon = Coupon.objects.get(
                code__iexact=code, 
                active=True, 
                valid_from__lte=timezone.now(), 
                valid_to__gte=timezone.now()
            )
            if subtotal < coupon.minimum_order_value:
                request.session['coupon_error'] = f"Minimum cart value of ₹{coupon.minimum_order_value} required."
            else:
                request.session['coupon_id'] = coupon.id
                request.session['coupon_error'] = None
                messages.success(request, f"Coupon '{coupon.code}' applied successfully!")
        except Coupon.DoesNotExist:
            request.session['coupon_error'] = "Invalid coupon code."
            
    return redirect('cart_detail')

def remove_coupon(request):
    if 'coupon_id' in request.session:
        del request.session['coupon_id']
        messages.info(request, "Coupon removed.")
    return redirect('cart_detail')

@staff_member_required
def manage_coupons(request):
    coupons = Coupon.objects.all().order_by('-id')
    return render(request, 'store/manage_coupons.html', {'coupons': coupons})

@staff_member_required
def add_coupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon created successfully!")
            return redirect('manage_coupons')
    else:
        form = CouponForm()
    return render(request, 'store/coupon_form.html', {'form': form, 'title': 'Create Coupon'})

@staff_member_required
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon updated successfully!")
            return redirect('manage_coupons')
    else:
        form = CouponForm(instance=coupon)
    return render(request, 'store/coupon_form.html', {'form': form, 'title': 'Edit Coupon'})

@staff_member_required
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    messages.success(request, "Coupon deleted successfully!")
    return redirect('manage_coupons')