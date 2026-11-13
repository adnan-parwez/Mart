from .models import Product

def categories_processor(request):
    # Get unique categories from the database
    categories = Product.objects.values_list('category', flat=True).distinct()
    # Clean the list and remove empty ones
    categories = [c.strip() for c in categories if c and c.strip()]
    return {'all_categories': categories}