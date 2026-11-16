from django.contrib import admin
from django.urls import path
from store import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views # 👈 Make sure this is here

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.shop, name='shop'),
    path('category/<path:category_name>/', views.category_view, name='category_view'),
    path('cart/update/<int:product_id>/<str:action>/', views.update_cart, name='update_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    path('pending/<int:order_id>/', views.pending_page, name='pending_page'),
    
    # 👇 MAKE SURE THIS LINE HAS A COMMA AT THE END 👇
    path('order/status/<int:order_id>/', views.order_status, name='order_status'),
    

    # Auth URLs
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Guest Password Setup
    path('set-password/<int:order_id>/', views.set_password_guest, name='set_password_guest'), # 👈 THIS LINE ALSO NEEDS A COMMA
    
    # Password Reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='store/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='store/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='store/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='store/password_reset_complete.html'), name='password_reset_complete'),

    # Dashboard URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/products/', views.manage_products, name='manage_products'),
    path('dashboard/products/add/', views.add_product, name='add_product'),
    path('dashboard/products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('dashboard/products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('dashboard/customers/', views.manage_customers, name='manage_customers'),
    path('dashboard/customers/edit/<int:user_id>/', views.edit_customer, name='edit_customer'),
    path('dashboard/customers/delete/<int:user_id>/', views.delete_customer, name='delete_customer'),
    path('dashboard/orders/', views.manage_orders, name='manage_orders'),
    path('dashboard/orders/confirm/<int:order_id>/', views.confirm_payment_and_send_invoice, name='confirm_payment'),
    path('dashboard/coupons/', views.manage_coupons, name='manage_coupons'),
    path('dashboard/coupons/add/', views.add_coupon, name='add_coupon'),
    path('dashboard/coupons/edit/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('dashboard/coupons/delete/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),

    # Profile & Wishlist
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('my-orders/invoice/<int:order_id>/', views.order_invoice, name='order_invoice'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('cart/move-to-wishlist/<int:product_id>/', views.move_to_wishlist, name='move_to_wishlist'),
    path('cart/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('cart/remove-coupon/', views.remove_coupon, name='remove_coupon'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)