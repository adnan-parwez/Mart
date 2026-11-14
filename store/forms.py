from django import forms
from .models import Product
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Product
from .models import CustomUser, Product

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email Address")
    phone = forms.CharField(required=True, label="Phone Number")
    first_name = forms.CharField(required=True, label="First Name")
    last_name = forms.CharField(required=False, label="Last Name")

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("first_name", "last_name", "email", "phone")

    # Custom check for duplicate email
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    # Custom check for duplicate phone
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if CustomUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError("An account with this phone number already exists.")
        return phone

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'mrp', 'category', 'image', 'description', 'stock'] 
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Name'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Selling Price (e.g., 200)'}),
            'mrp': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'MRP (e.g., 300)'}), # Add styling
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category (e.g., Grocery)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Stock Quantity (e.g., 50)'}),
        }



