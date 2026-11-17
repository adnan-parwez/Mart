from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, BaseUserManager

# 1. Create the Custom Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

# 2. Update your CustomUser Model
class CustomUser(AbstractUser):
    username = None # Remove username
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] 

    # 👇 TELL DJANGO TO USE THE CUSTOM MANAGER
    objects = CustomUserManager() 

    def __str__(self):
        return self.email

    
class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address_line = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.full_name} - {self.city}"

    
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    description = models.TextField(blank=True)
    stock = models.IntegerField(default=10)

    def __str__(self):
        return self.name

    @property
    def discount_percentage(self):
        if self.mrp and self.mrp > self.price:
            # Math: ((MRP - Price) / MRP) * 100
            discount = ((self.mrp - self.price) / self.mrp) * 100
            return int(discount)
        return 0

# 3. Order Model
class Order(models.Model):
    order_number = models.CharField(max_length=20, blank=True)

    # --- Customer / shipping ---
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orders'
    )
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)

    address = models.TextField(blank=True)         # store pickup uses a long string
    city = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)

    # --- Payment ---
    payment_method = models.CharField(max_length=50, blank=True)
    is_paid = models.BooleanField(default=False)

    # --- Totals ---
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            today = timezone.now().strftime('%d%m%Y')
            last_order = Order.objects.filter(
                order_number__startswith=today
            ).order_by('-order_number').first()
            new_sequence = (
                int(last_order.order_number[-3:]) + 1 if last_order else 1
            )
            self.order_number = f"{today}{new_sequence:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number} - {self.first_name}"


# 4. Order Item Model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class Coupon(models.Model):
    DISCOUNT_TYPES = (
        ('percentage', 'Percentage (%)'),
        ('flat', 'Flat Amount (₹)'),
    )
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Enter 10 for 10% or 50 for ₹50")
    minimum_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Minimum cart value required to use this coupon")
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    def __str__(self):
        if self.discount_type == 'percentage':
            return f"{self.code} - {self.discount_value}% off"
        return f"{self.code} - ₹{self.discount_value} off"
    
from django import forms
from .models import Coupon

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_type', 'discount_value', 'minimum_order_value', 'active', 'valid_from', 'valid_to']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. RUMI10'}),
            'discount_type': forms.Select(attrs={'class': 'form-control'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'minimum_order_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'valid_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


