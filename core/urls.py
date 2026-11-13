from django.contrib import admin
from django.urls import path
from store import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.shop, name='shop'),
    path('category/<str:category_name>/', views.category_view, name='category_view'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    
    # Success & Pending
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    path('pending/<int:order_id>/', views.pending_page, name='pending_page'),
    
    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Admin Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/products/', views.manage_products, name='manage_products'),
    path('dashboard/products/add/', views.add_product, name='add_product'),
    path('dashboard/products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('dashboard/products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('dashboard/customers/', views.manage_customers, name='manage_customers'),
    
    # Order Management
    path('dashboard/orders/', views.manage_orders, name='manage_orders'),
    path('dashboard/orders/confirm/<int:order_id>/', views.confirm_payment_and_send_invoice, name='confirm_payment'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)