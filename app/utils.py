import random
from decimal import Decimal, InvalidOperation
from django.db import models
from django.utils import timezone
from accounts.models import Offer


def generate_otp():
    return "".join([str(random.randint(0, 9)) for _ in range(6)])


def calculate_cart_totals(cart_items, coupon=None):
    try:
        subtotal = Decimal("0.00")
        total_qty = 0

        for item in cart_items:
            product = item.product_variant.product
            base_price = item.product_variant.price or Decimal("0.00")
            discount_percentage = get_product_discount(product) or 0
            discounted_price = base_price - (base_price * discount_percentage / 100)

            item_total = discounted_price * item.quantity
            subtotal += item_total
            total_qty += item.quantity

        coupon_discount = Decimal("0.00")
        if coupon and coupon.discount_percentage:
            coupon_discount = subtotal * Decimal(coupon.discount_percentage) / 100

        shipping = Decimal("0.00") if subtotal >= Decimal("30.00") else Decimal("4.99")

        final_total = subtotal - coupon_discount + shipping

        return {
            "subtotal": round(subtotal or Decimal("0.00"), 2),
            "total_qty": total_qty,
            "coupon_discount": round(coupon_discount or Decimal("0.00"), 2),
            "shipping": round(shipping or Decimal("0.00"), 2),
            "final_total": round(final_total or Decimal("0.00"), 2),
        }

    except (InvalidOperation, TypeError) as e:
        return {
            "subtotal": Decimal("0.00"),
            "total_qty": 0,
            "coupon_discount": Decimal("0.00"),
            "shipping": Decimal("0.00"),
            "final_total": Decimal("0.00"),
            "error": str(e),
        }


def get_product_discount(product):
    today = timezone.now().date()

    offers = (
        Offer.objects.filter(is_active=True, valid_from__lte=today, valid_to__gte=today)
        .filter(models.Q(product=product) | models.Q(category=product.category))
        .order_by("-discount_percent")
    )

    if offers.exists():
        return offers.first().discount_percent
    return Decimal(0)


def get_discounted_price(product):
    price = Decimal(product.price or 0)
    discount = get_product_discount(product)

    if discount > 0:
        discounted_price = price - (price * discount / Decimal(100))
        return discounted_price.quantize(Decimal("0.01"))
    return price
