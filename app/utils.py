import random

def generate_otp():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])



from decimal import Decimal,InvalidOperation
from django.db.models import Sum
from app.models import Cart ,Coupon 





def calculate_cart_totals(cart_items, coupon=None):
    try:
        subtotal = Decimal('0.00')
        total_qty = 0

        for item in cart_items:
            product = item.product_variant.product
            base_price = item.product_variant.price or Decimal('0.00')
            discount_percent = get_product_discount(product) or 0
            discounted_price = base_price - (base_price * discount_percent / 100)

            item_total = discounted_price * item.quantity
            subtotal += item_total
            total_qty += item.quantity

        # Apply coupon if provided
        coupon_discount = Decimal('0.00')
        if coupon and coupon.discount_percentage:
            coupon_discount = subtotal * Decimal(coupon.discount_percentage) / 100

        # Shipping logic
        shipping = Decimal('0.00') if subtotal >= Decimal('30.00') else Decimal('4.99')

        final_total = subtotal - coupon_discount + shipping

        return {
            'subtotal': round(subtotal or Decimal('0.00'), 2),
            'total_qty': total_qty,
            'coupon_discount': round(coupon_discount or Decimal('0.00'), 2),
            'shipping': round(shipping or Decimal('0.00'), 2),
            'final_total': round(final_total or Decimal('0.00'), 2)
        }
    
    except (InvalidOperation, TypeError) as e:
        return {
            'subtotal': Decimal('0.00'),
            'total_qty': 0,
            'coupon_discount': Decimal('0.00'),
            
            'shipping': Decimal('0.00'),
            'final_total': Decimal('0.00'),
            'error': str(e)
        }



from accounts.models import CategoryOffer, ProductOffer
from django.utils import timezone

def get_product_discount(product):
    category_offer = CategoryOffer.objects.filter(
        category=product.category,
        is_active=True,
        valid_from__lte=timezone.now().date(),
        valid_to__gte=timezone.now().date()
    ).order_by('-discount_percent').first()

    product_offer = ProductOffer.objects.filter(
        product=product,
        is_active=True,
        valid_from__lte=timezone.now().date(),
        valid_to__gte=timezone.now().date()
    ).order_by('-discount_percent').first()

    category_discount = category_offer.discount_percent if category_offer else 0
    product_discount = product_offer.discount_percent if product_offer else 0

    return max(category_discount, product_discount)

def get_discounted_price(product):
    discount = get_product_discount(product)
    return product.price - (product.price * discount / 100)
