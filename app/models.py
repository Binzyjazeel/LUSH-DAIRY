from django.db import models
from accounts.models import Product, ProductImage, ProductVariant, CustomUser
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from cloudinary_storage.storage import MediaCloudinaryStorage


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)


class Review(models.Model):
    RATING_CHOICES = [
        (5, "★★★★★ 5 - Excellent"),
        (4, "★★★★☆ 4 - Good"),
        (3, "★★★☆☆ 3 - Average"),
        (2, "★★☆☆☆ 2 - Poor"),
        (1, "★☆☆☆☆ 1 - Bad"),
    ]
    product = models.ForeignKey(
        Product, related_name="reviews", on_delete=models.CASCADE
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on {self.product.name}"


class UserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="profile"
    )
    profile_image = models.ImageField(storage=MediaCloudinaryStorage(),
        upload_to="profiles/", default="profiles/default.jpeg"
    )
    bio = models.TextField(max_length=500, blank=True)
    mobile = models.CharField(max_length=15, blank=True)
    loyalty_points = models.IntegerField(default=0)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Address(models.Model):
    ADDRESS_TYPES = [
        ("home", "Home"),
        ("office", "Office"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="addresses"
    )
    address_type = models.CharField(
        max_length=20, choices=ADDRESS_TYPES, default="home"
    )
    street = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="India")
    pincode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.get_address_type_display()} - {self.user.username}"

    def get_address_type_display(self):
        return dict(self.ADDRESS_TYPES)[self.address_type]

    def save(self, *args, **kwargs):
        if self.is_default:

            Address.objects.filter(user=self.user, is_default=True).update(
                is_default=False
            )
        super().save(*args, **kwargs)


class Order(models.Model):
    ORDER_STATUS = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("returned", "Returned"),
        ("Partially Cancelled", "Partially Cancelled"),
        ("Resolved", "Resolved"),
    ]
    RETURN_STATUS_CHOICES = [
        ("not_requested", "Not Requested"),
        ("requested", "Requested"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="orders"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=True, blank=True
    )
    order_id = models.CharField(max_length=20, unique=True)
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default="pending")
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_method = models.CharField(max_length=50, default="COD")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    return_status = models.CharField(
        max_length=20,
        choices=RETURN_STATUS_CHOICES,
        default="not_requested",
        blank=True,
    )
    address_name = models.CharField(max_length=100, default="")
    address_phone = models.CharField(max_length=15, default="")
    address_line1 = models.CharField(max_length=255, default="")
    address_line2 = models.CharField(max_length=255, blank=True, default="")
    address_city = models.CharField(max_length=100, default="")
    address_state = models.CharField(max_length=100, default="")
    address_zipcode = models.CharField(max_length=10, default="")
    coupon = models.ForeignKey(
        "Coupon", null=True, blank=True, on_delete=models.SET_NULL
    )
    wallet_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order_id} - {self.user.username}"

    def get_absolute_url(self):
        return reverse("user_panel:order_detail", kwargs={"order_id": self.id})


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    created_at = models.DateTimeField(default=timezone.now)
    product_variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, null=True, blank=True
    )
    product_name = models.CharField(max_length=200)
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True
    )
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    cancel_reason = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("Pending", "Pending"),
            ("Cancelled", "Cancelled"),
            ("Delivered", "Delivered"),
            ("Returned", "Returned"),
        ],
        default="Pending",
    )

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    @property
    def total_price(self):
        return self.quantity * self.price


class Cart(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="cart_items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=True, blank=True
    )
    product_variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, default=1
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def get_price(self):
        return self.product_variant.price

    def total_price(self):
        return self.quantity * self.product_variant.price

    def __str__(self):
        return f"{self.user.username} - {self.product.name} (x{self.quantity})"


class Wishlist(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="wishlist_items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user.username} → {self.product.name}"


class ReturnRequest(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, null=True, blank=True
    )
    reason = models.TextField()
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    verified = models.BooleanField(default=False)
    refunded = models.BooleanField(default=False)
    requested_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(storage=MediaCloudinaryStorage(),upload_to="complaint_images/", blank=True, null=True)

    def __str__(self):
        return f"ReturnRequest #{self.id} for Order {self.order.order_id}"


class Wallet(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def credit(self, amount):
        self.balance += amount
        self.save()


class WalletTransaction(models.Model):
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="transactions"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(
        max_length=10, choices=[("credit", "Credit"), ("debit", "Debit")]
    )
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} ₹{self.amount} - {self.wallet.user.email}"


class Payment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[("PENDING", "Pending"), ("SUCCESS", "Success"), ("FAILED", "Failed")],
        default="PENDING",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.status}"


class Coupon(models.Model):
    users = models.ManyToManyField(CustomUser, blank=True)
    used_users = models.ManyToManyField(
        CustomUser, blank=True, related_name="redeemed_coupons"
    )
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.PositiveIntegerField()
    valid_from = models.DateField()
    valid_to = models.DateField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code
