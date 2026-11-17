from .models import Product
from .models import Order

def categories_processor(request):
    # Get unique categories from the database
    categories = Product.objects.values_list('category', flat=True).distinct()
    # Clean the list and remove empty ones
    categories = [c.strip() for c in categories if c and c.strip()]
    return {'all_categories': categories}


def pending_orders_alert(request):
    if request.user.is_authenticated and request.user.is_staff:
        # Check if there are any unpaid orders
        has_pending = Order.objects.filter(is_paid=False).exists()
        return {'global_has_pending': has_pending}
    return {'global_has_pending': False}