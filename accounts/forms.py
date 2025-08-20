from django import forms
from .models import Category
from .models import Product,CustomUser
from app.models import Coupon,ProductImage


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'number_of_products','image', 'status', 'discount_percentage', 'offer_text']

    def clean_name(self):
        name = self.cleaned_data.get('name')

        
        qs = Category.objects.filter(name__iexact=name.strip(), is_deleted=False)

       
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("This category already exists.")

        return name
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'description','composition','main_image','images','discounted_price','category']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter title'}),
        }
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        category = cleaned_data.get('category')
        if Product.objects.filter(name__iexact=name, category=category).exists():
            raise forms.ValidationError("This product already exists in this category.")
        return cleaned_data
from .models import ProductVariant

class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['product', 'variant_name', 'price', 'stock', 'is_active']

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        variant_name = cleaned_data.get('variant_name')

        if product and variant_name:
        
            qs = ProductVariant.objects.filter(
                product=product,
                variant_name__iexact=variant_name
        )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                self.add_error(
                'variant_name',
                f"A variant named '{variant_name}' already exists for this product."
            )
   
        return cleaned_data


from .models import Address

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['address_type', 'street', 'city', 'state', 'pincode','country','is_default']

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'mobile', 'profile_image']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
        }
from django import forms
from app.models import Coupon
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

class CouponForm(forms.ModelForm):
    users = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Coupon
        fields = '__all__'
        widgets = {
            'valid_from': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valid_to': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


from django import forms
from .models import Offer

class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['name', 'discount_percent', 'valid_from', 'valid_to', 'is_active', 'product', 'category']
        widgets = {
            'valid_from': forms.DateInput(attrs={'type': 'date'}),
            'valid_to': forms.DateInput(attrs={'type': 'date'}),
        }


    
    