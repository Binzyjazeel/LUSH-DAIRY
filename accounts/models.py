from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.templatetags.static import static 
import uuid
import os

class CustomUser(AbstractUser):
    is_user = models.BooleanField(default=False)
    is_panel_staff = models.BooleanField(default=False) 
    referral_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    is_admin_user = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now) 
    mobile = models.CharField(max_length=15, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', default='profiles/default.jpeg')
    bio = models.TextField(blank=True)
    pending_email = models.EmailField(blank=True, null=True)
    email_otp = models.CharField(max_length=6, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def generate_referral_code(self):
        return str(uuid.uuid4()).split('-')[0].upper()  # e.g., '5GHT21K8'

class CategoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class Category(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_deleted = models.BooleanField(default=False)
    number_of_products = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    offer_text = models.CharField(max_length=255, blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
   
    objects = CategoryManager() 
    all_objects = models.Manager() 

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255, default="Unnamed Product")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(blank=True, default="No description available.")
    composition = models.TextField(blank=True, default="No description available.")
    
  
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    is_deleted = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    is_listed = models.BooleanField(default=True)
    average_rating = models.FloatField(default=0.0)
    specs = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    

    main_image = models.ImageField(upload_to='products/', blank=True, null=True, default='default.jpeg')
    images = models.ImageField(upload_to='product_images/', blank=True, null=True)

    def final_price(self):
        return self.price * (1 - self.discounted_price / 100)

    def __str__(self):
        return self.name

    @property
    def stock(self):
        return self.variants.aggregate(total=models.Sum('stock'))['total'] or 0

    @property
    def is_available(self):
        return self.stock > 0

    @property
    def main_image_url(self):
        if self.main_image:
            return self.main_image.url
        return static('images/default.jpeg')


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='uploadimage')
    image = models.ImageField(upload_to='product_images/')
    def __str__(self):
        return f"{self.product.name} - Image"




class ProductSpec(models.Model):
    product = models.ForeignKey(Product, related_name='product_specs', on_delete=models.CASCADE)
    detail = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.product.name} - {self.detail}"
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    variant_name = models.CharField(max_length=100)  
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'variant_name'], name='unique_variant_per_product')
        ]

    def __str__(self):
        return f"{self.product.name} - {self.variant_name}"
class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    street = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default='India')
    address_type = models.CharField(max_length=50, choices=[('home', 'Home'), ('office', 'Office')], default='home')
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.street}, {self.city}, {self.state} - {self.pincode}"
from django.core.validators import MaxValueValidator, MinValueValidator
   
# For Offer Types
class CategoryOffer(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    discount_percent = models.PositiveIntegerField(validators=[MaxValueValidator(100)])
    valid_from = models.DateField()
    valid_to = models.DateField()
    is_active = models.BooleanField(default=True)

class ProductOffer(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    discount_percent = models.PositiveIntegerField(validators=[MaxValueValidator(100)])
    valid_from = models.DateField()
    valid_to = models.DateField()
    is_active = models.BooleanField(default=True)



   


