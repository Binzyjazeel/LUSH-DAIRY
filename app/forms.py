

from django import forms
from .models import Review

class EmailForm(forms.Form):
    email = forms.EmailField()

class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6)

class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import Address, UserProfile,ReturnRequest,Wallet

class ProfileForm(forms.ModelForm):
    profile_image = forms.ImageField(required=False)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your last name'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['bio'].initial = self.instance.profile.bio

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.bio = self.cleaned_data.get('bio', '')
            if self.cleaned_data.get('profile_image'):
                profile.profile_image = self.cleaned_data['profile_image']
            profile.save()
        return user

class AddressForm(forms.ModelForm):
    ADDRESS_TYPES = [
        ('home', 'Home'),
        ('office', 'Office'),
        ('other', 'Other'),
    ]
    
    address_type = forms.ChoiceField(choices=ADDRESS_TYPES, widget=forms.Select(attrs={
        'class': 'form-control'
    }))
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        is_default = cleaned_data.get('is_default')

        if self.user and is_default:
           
            default_exists = Address.objects.filter(user=self.user, is_default=True)
            if self.instance.pk:
                default_exists = default_exists.exclude(pk=self.instance.pk)

            if default_exists.exists():
                raise forms.ValidationError("You already have a default address. Unset it before setting a new one.")

        return cleaned_data
    class Meta:  # ✅ You missed this part
        model = Address
        fields = [
            'address_type', 'street', 'city', 'state',
            'country', 'pincode', 'is_default'
        ]

class EmailChangeForm(forms.Form):
    new_email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter new email address'
    }))

class OTPVerificationForm(forms.Form):
    otp_1 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={
        'class': 'otp-input',
        'maxlength': '1',
        'pattern': '[0-9]'
    }))
    otp_2 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={
        'class': 'otp-input',
        'maxlength': '1',
        'pattern': '[0-9]'
    }))
    otp_3 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={
        'class': 'otp-input',
        'maxlength': '1',
        'pattern': '[0-9]'
    }))
    otp_4 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={
        'class': 'otp-input',
        'maxlength': '1',
        'pattern': '[0-9]'
    }))
    otp_5 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={
        'class': 'otp-input',
        'maxlength': '1',
        'pattern': '[0-9]'
    }))
    otp_6 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={
        'class': 'otp-input',
        'maxlength': '1',
        'pattern': '[0-9]'
    }))

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email address'
    }))
class ReturnRequestForm(forms.ModelForm):
    class Meta:
        model = ReturnRequest
        fields = ['reason']
