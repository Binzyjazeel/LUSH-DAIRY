from django.shortcuts import redirect,render
from django.contrib import messages
import random
from accounts.models import CustomUser,Product,ProductImage
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from .models import PasswordResetOTP,Review,Order,OrderItem,Wallet,WalletTransaction
from .forms import EmailForm, OTPForm, ResetPasswordForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import user_passes_test

def not_superuser(user):
    return not user.is_superuser

@user_passes_test(not_superuser, login_url='user_panel:login')
def signup_view(request):
    if request.method == "GET" and "ref" in request.GET:
        request.session["referral_code_from_link"] = request.GET["ref"]
    if request.method=="POST":
        username=request.POST["username"]
        email=request.POST["email"]
        password1=request.POST["password1"]
        password2=request.POST["password2"]
        
        referral_code = request.POST.get("referral") or request.session.get("referral_code_from_link")

        referrer=None
        if referral_code:
            try:
                referrer = CustomUser.objects.get(referral_code=referral_code)
                request.session["referrer_id"] = referrer.id
            except CustomUser.DoesNotExist:
                messages.error(request, "Invalid referral code")
                return redirect('user_panel:signup')
        if not all([username, email, password1, password2]):
            messages.error(request, "All fields are required.")
            return redirect('user_panel:signup')

        request.session["username"]=username
        request.session["email"]=email
        request.session["password1"]=password1
        if request.method == "GET" and "ref" in request.GET:
            request.session["referral_code_from_link"] = request.GET["ref"]


        if password1==password2:
            if CustomUser.objects.filter(username=username).exists():
                messages.info(request,"username already taken")
                return redirect('user_panel:signup')
            
            else:
                send_otp(request)
                return render(request,'user_panel/verify_otp.html',{"email":email})
        else:
            messages.info(request,"password mismatch")
            return redirect ('user_panel:signup')
    return render(request,"user_panel/signup.html")
def send_otp(request):
    otp = "".join([str(random.randint(0, 9)) for _ in range(4)])
    request.session["otp"] = otp

    email = request.session.get("email")
    print("Sending OTP to:", email) 
    if email:
        send_mail(
            "Your OTP for Sign Up",
            f"Your OTP is: {otp}",
            'djangoalerts0011@gmail.com', 
            [email],                       
            fail_silently=False,
        )



from decimal import Decimal

from decimal import Decimal

def otp_verification(request):
    if not all(k in request.session for k in ["username", "email", "password1"]):
        messages.error(request, "Session expired. Please try signing up again.")
        return redirect('user_panel:signup')

    if request.method == "POST":
        otp_ = request.POST.get("otp")
        if otp_ == request.session.get("otp"):
            encrypted_password = make_password(request.session['password1'])

            # ✅ Create new user
            nameuser = CustomUser(
                username=request.session["username"],
                email=request.session["email"],
                password=encrypted_password,
                is_active=True
            )

            referrer_id = request.session.get("referrer_id")
            if referrer_id:
                nameuser.referred_by_id = referrer_id

            nameuser.save()

            # ✅ Credit referral bonus only first time
            if referrer_id:
                wallet, _ = Wallet.objects.get_or_create(user_id=referrer_id)
                if not WalletTransaction.objects.filter(
                    wallet=wallet,
                    description__icontains=f"Referral bonus for {nameuser.username}"
                ).exists():
                    wallet.credit(Decimal("50.00"))

                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type="credit",
                        amount=Decimal("50.00"),
                        description=f"Referral bonus for {nameuser.username}"
                    )

            # ✅ Clear session
            for key in ["username", "email", "password1", "referrer_id", "otp"]:
                request.session.pop(key, None)

            messages.success(request, "Account created successfully!")
            return redirect('user_panel:login')

        messages.error(request, "OTP doesn't match, please try again!")

    return render(request, "user_panel/verify_otp.html")



def logout_view(request):
    request.session.flush()
    logout(request)
    
    return redirect('user_panel:login')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            
            if getattr(user, 'is_blocked', False):
                messages.error(request, "Your account has been blocked by the admin.")
                return redirect('user_panel:login')

           
            if user.is_superuser or user.is_staff or getattr(user, 'is_admin_user', False):
                messages.error(request, "Admin users cannot log in from the user panel.")
                return redirect('user_panel:login')

            
            login(request, user)
            return redirect('user_panel:home')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('user_panel:login')

    return render(request, 'user_panel/login.html')
@never_cache
def home(request):
    return render(request, 'user_panel/home.html')

def resend_otp(request):
    if request.method == "POST":
        email = request.session.get("email")
        if not email:
            user_id = request.session.get("reset_user_id")
            if not user_id:
                return JsonResponse({"error": "Session expired. Please restart process."}, status=400)
            try:
                user = CustomUser.objects.get(id=user_id)
                email = user.email
            except CustomUser.DoesNotExist:
                return JsonResponse({"error": "User not found."}, status=404)
        otp = "".join([str(random.randint(0, 9)) for _ in range(4)])
        request.session["otp"] = otp
        
        send_mail(
            "Your New OTP",
            f"Your new OTP is {otp}",
            'djangoalerts0011@gmail.com',
            [email],
            fail_silently=False
        )
        print("Session email before resend:", request.session.get("email"))

        return JsonResponse({"success": True, "message": "OTP resent successfully."})
    
    return JsonResponse({"error": "Invalid request method"}, status=405)

def generate_otp():
    return str(random.randint(100000, 999999))

def forgot_password_request(request):
    

    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            users = CustomUser.objects.filter(email=email)

            if users.exists():
                user = users.first()  

              
                otp = generate_otp()
                PasswordResetOTP.objects.create(user=user, otp=otp)

           
                request.session['reset_user_id'] = user.id
                print(f"[DEBUG] Session set for user: {user.username} | ID: {user.id}")

                
                send_mail(
                    'Your OTP for Password Reset',
                    f'Your OTP is: {otp}',
                    'noreply@example.com',
                    [email],
                    fail_silently=False,
                )

                return redirect('user_panel:otp_verify')
            else:
                messages.error(request, 'No user found with that email.')
        else:
            messages.error(request, 'Invalid form input.')
    else:
        form = EmailForm()

    return render(request, 'user_panel/forgot_password.html', {'form': form})



def otp_verify(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, "Session expired. Please try again.")
        return redirect('user_panel:forgot_password')

    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, "User does not exist.")
        return redirect('user_panel:forgot_password')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            otp_input = form.cleaned_data['otp']
            try:
                otp_entry = PasswordResetOTP.objects.filter(user=user, otp=otp_input).latest('created_at')
                if otp_entry.is_expired():
                    messages.error(request, 'OTP has expired.')
                else:
                    
                    request.session['otp_verified'] = True
                    request.session['reset_user_id'] = user.id 
                    return redirect('user_panel:reset_password')
            except PasswordResetOTP.DoesNotExist:
                messages.error(request, 'Invalid OTP.')
    else:
        form = OTPForm()

    return render(request, 'user_panel/otp_verify.html', {'form': form})
def resend_reset_password_otp(request):
    if request.method == "POST":
        user_id = request.session.get("reset_user_id")
        if not user_id:
            return JsonResponse({"error": "Session expired. Please restart password reset."}, status=400)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=404)

        otp = generate_otp()
        PasswordResetOTP.objects.create(user=user, otp=otp)

        send_mail(
            "Your New OTP for Password Reset",
            f"Your new OTP is {otp}",
            'djangoalerts0011@gmail.com',
            [user.email],
            fail_silently=False
        )

        return JsonResponse({"success": True, "message": "OTP resent successfully."})

    return JsonResponse({"error": "Invalid request method"}, status=405)


def reset_password(request):
    if not request.session.get('otp_verified'):
        return redirect('user_panel:forgot_password')

    user_id = request.session.get('reset_user_id')
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('user_panel:forgot_password')

    if request.method == 'POST':
        pwd1 = request.POST.get('new_password')
        pwd2 = request.POST.get('confirm_password')

        if pwd1 != pwd2:
            messages.error(request, 'Passwords do not match.')
        else:
            user.set_password(pwd1)
            user.save()
            from django.contrib.auth import authenticate
           
            auth_user = authenticate(username=user.username, password=pwd1)
            print("Authentication test after reset:", auth_user)

            user.save()
            print("New password hash:", user.password)
            print("Resetting password for:", user.username)


            logout(request)
           
            request.session.pop('reset_user_id', None)
            request.session.pop('otp_verified', None)
            

            messages.success(request, 'Password reset successful.')
            return redirect('user_panel:login')

    return render(request, 'user_panel/set_new_password.html')


from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from accounts.models import Product, Category,Address,Offer
from .utils import get_discounted_price
@never_cache
def product_list(request):
    products = Product.objects.filter(is_deleted=False, is_listed=True)
    
    

   
    query = request.GET.get('q')
    products = Product.objects.filter(is_deleted=False)
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

   
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    
    sort_by = request.GET.get('sort')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'az':
        products = products.order_by('name')
    elif sort_by == 'za':
        products = products.order_by('-name')
    elif sort_by == 'popularity':
        products = products.order_by('-popularity_score')
    elif sort_by == 'rating':
        products = products.order_by('-average_rating')
    elif sort_by == 'new':
        products = products.order_by('-created_at')

    
    paginator = Paginator(products, 5)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    for product in page_obj:
        product.discounted_price = get_discounted_price(product)


    context = {
        'products': page_obj,
        'categories': Category.objects.all(),
        'query': query,
        'selected_category': category_id,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'page_obj': page_obj,
        
       
    }
    return render(request, 'user_panel/product_list.html', context)

from django.shortcuts import render, get_object_or_404
from accounts.models import Product, ProductImage,ProductVariant,Address
from django.templatetags.static import static
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.templatetags.static import static
from django.utils import timezone
@never_cache
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    discounted_price = get_discounted_price(product)
    variants = ProductVariant.objects.filter(product=product)
    offer = Offer.objects.filter(
        product=product,
        is_active=True,
        valid_from__lte=timezone.now().date(),
        valid_to__gte=timezone.now().date()
    ).first()

    # If no product-specific offer, check category offer
    if not offer and product.category:
        offer = Offer.objects.filter(
            category=product.category,
            is_active=True,
            valid_from__lte=timezone.now().date(),
            valid_to__gte=timezone.now().date()
        ).first()
    variant_id = request.GET.get('variant_id')
    if variant_id:
        selected_variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
    else:
        selected_variant = variants.first() 
    if not selected_variant:
        messages.error(request, "No variants available for this product.")
        


   
    if (product.is_blocked or product.is_deleted or not product.is_listed or not selected_variant or selected_variant.stock <= 0):

        messages.error(request, "Sorry, this product is currently unavailable.")
        return redirect('user_panel:userproduct_list')

   
    images = ProductImage.objects.filter(product=product)
   
    if product.main_image and product.main_image.name:
        images = images.exclude(image=product.main_image.name)

    
    if product.main_image and product.main_image.url:
        main_image_url = product.main_image.url
    else:
        main_image_url = static('images/default.jpeg')

   
    reviews = Review.objects.filter(product=product).order_by('-created_at')
    
   
    related_products = Product.objects.filter(
    category=product.category,
    is_deleted=False,
    is_blocked=False,
    is_listed=True,
    ).annotate(
        total_stock=Sum('variants__stock')
    
).exclude(id=product.id)[:4]

    
    coupons = Coupon.objects.filter(active=True)

    context = {
        'product': product,
        'main_image_url': main_image_url,
        'images': images,
        'reviews': reviews,
        'related_products': related_products,
        'coupons': coupons,
        'variants': variants,
        'selected_variant': selected_variant,
        'discounted_price': discounted_price,
        'offer': offer,
        
        
    }

    return render(request, 'user_panel/product_detail.html', context)



from .models import Product, Review
from .forms import ReviewForm

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        existing_review = Review.objects.get(product=product, user=request.user)
    except Review.DoesNotExist:
        existing_review = None

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=existing_review)

        if product.is_deleted or product.is_blocked or not product.is_available:
            messages.warning(request, "You cannot review this product right now.")
            return redirect('user_panel:product_list')

        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            messages.success(request, "Your review has been submitted successfully!")
            return redirect('user_panel:product_detail', pk=product.id)
    else:
        form = ReviewForm(instance=existing_review)

    return render(request, 'user_panel/add_review.html', {
        'product': product,
        'form': form,
        'existing_review': existing_review
    })




from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.core.cache import cache
import json
from .models import UserProfile, Address, Order
from .forms import ProfileForm, AddressForm, EmailChangeForm
@never_cache
@login_required
def profile_view(request):
  
    tab = request.GET.get('tab', 'profile')
    user = request.user
    addresses = Address.objects.filter(user=user)
    primary_address = addresses.filter(is_default=True).first()
    orders = Order.objects.filter(user=user).order_by('-created_at')
    referral_code = request.user.referral_code
    referral_link = request.build_absolute_uri(
        reverse('user_panel:signup') + f"?ref={request.user.referral_code}"
    )
   
    total_orders = orders.count()
    active_orders = orders.filter(status__in=['pending', 'processing']).count()
    loyalty_points = getattr(user.profile, 'loyalty_points', 0) if hasattr(user, 'profile') else 0
    
    context = {
        'user': user,
        'addresses': addresses,
        'primary_address': primary_address,
        'orders': orders,
        'total_orders': total_orders,
        'active_orders': active_orders,
        'loyalty_points': loyalty_points,
        'active_tab': tab,
        'profile_form': ProfileForm(instance=user),
        'address_form': AddressForm(),
        'password_form': PasswordChangeForm(user),
        'referral_code': referral_code,
        'referral_link': referral_link,
    }
    
    return render(request, 'user_panel/user_profile.html', context)

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import random
from django.core.mail import send_mail
from django.conf import settings



@login_required
def edit_profile(request):
    user = request.user

    if request.method == 'POST':
        new_name = request.POST.get('name')
        new_email = request.POST.get('email')
        new_mobile = request.POST.get('mobile')
        new_bio = request.POST.get('bio')

        if new_email != user.email:
            otp = str(random.randint(100000, 999999))
            user.pending_email = new_email
            user.email_otp = otp
            user.save()

            send_mail(
                subject='Verify your new email address',
                message=f'Your OTP is {otp}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[new_email],
            )
            messages.info(request, "An OTP has been sent to your new email. Please verify to complete changes.")
            return redirect('user_panel:verify_email')

       
        user.username = new_name
        user.mobile = new_mobile
        user.bio = new_bio
        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('/profile#edit')

    return redirect('/profile#edit')


@login_required
def verify_email(request):
    user = request.user
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        if entered_otp == user.email_otp:
            user.email = user.pending_email
            user.pending_email = ''
            user.email_verified = True
            user.email_otp = ''
            user.save()
            messages.success(request, "Email verified and updated.")
            return redirect('/profile#edit')
        else:
            messages.error(request, "Invalid OTP.")
    return render(request, 'user_panel/verify_email.html')


from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import random


def resend_email_otp(request):
    if request.user.is_authenticated:
        new_email = request.session.get('new_email')
        if not new_email:
            messages.error(request, "No pending email change found.")
            return redirect('/profile#edit')

        otp = random.randint(100000, 999999)
        request.session['email_otp'] = otp

      
        send_mail(
            'Your Lush Dairy Email Verification OTP',
            f'Your OTP for verifying your new email address is: {otp}',
            settings.DEFAULT_FROM_EMAIL,
            [new_email],
            fail_silently=False,
        )

        messages.success(request, f"OTP has been resent to {new_email}.")
        return redirect('user_panel:verify_email')
    else:
        return redirect('user_panel:login')



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Address  
@never_cache
@login_required
def profile_view(request):
    """Main profile view with all tabs"""
    addresses = Address.objects.filter(user=request.user)
    primary_address = addresses.filter(is_default=True).first()
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'addresses': addresses,
        'primary_address': primary_address,
        'user': request.user,
        'orders':orders,
    }
    return render(request, 'user_panel/user_profile.html', context)
@never_cache
@login_required
def add_address(request):
    """Add new address"""
    if request.method == 'POST':
        address_type = request.POST.get('address_type')
        street = request.POST.get('street')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country')
        pincode = request.POST.get('pincode')
        is_default = request.POST.get('is_default') == 'true'

        
        if not all([address_type, street, city, state, country, pincode]):
            messages.error(request, 'All fields are required.')
            return redirect('/profile#address')

        
        if is_default:
            existing_default = Address.objects.filter(user=request.user, is_default=True)
            if existing_default.exists():
                messages.error(request, "You already have a default address. Please unset it first.")
                return redirect('/profile#address')

      
        Address.objects.create(
            user=request.user,
            address_type=address_type,
            street=street,
            city=city,
            state=state,
            country=country,
            pincode=pincode,
            is_default=is_default
        )

        messages.success(request, 'Address added successfully!')
        return redirect('/profile#address')

    return redirect('/profile#address')
@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == 'POST':
        address.address_type = request.POST.get('address_type')
        address.street = request.POST.get('street')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.country = request.POST.get('country')
        address.pincode = request.POST.get('pincode')
        is_default = request.POST.get('is_default') == 'true'

      
        if not all([address.address_type, address.street, address.city, 
                    address.state, address.country, address.pincode]):
            messages.error(request, 'All fields are required.')
            return render(request, 'user_panel/edit_address.html', {'address': address})

      
        if is_default and not address.is_default:
            existing_default = Address.objects.filter(user=request.user, is_default=True).exclude(id=address.id)
            if existing_default.exists():
                messages.error(request, "You already have a default address. Please unset it first.")
                return render(request, 'user_panel/edit_address.html', {'address': address})
            address.is_default = True
        elif not is_default and address.is_default:
            address.is_default = False

        address.save()
        messages.success(request, 'Address updated successfully!') 
        return redirect('/profile#address')

    return render(request, 'user_panel/edit_address.html', {'address': address})


@login_required
def delete_address(request, address_id):
   
    if request.method == 'POST':
        address = get_object_or_404(Address, id=address_id, user=request.user)
        
        
        if address.is_default:
            
            other_address = Address.objects.filter(user=request.user).exclude(id=address_id).first()
            if other_address:
                other_address.is_default = True
                other_address.save()
        
        address.delete()
        messages.success(request, 'Address deleted successfully!')
    
    return redirect('/profile#address')



@login_required
def set_default_address(request, address_id):
    """Set selected address as default if it's not already"""

    if request.method == 'POST':
        address = get_object_or_404(Address, id=address_id, user=request.user)

       
        if address.is_default and not Address.objects.filter(user=request.user, is_default=True).exclude(id=address.id).exists():
            messages.info(request, "This address is already set as your default.")
        else:
           
            Address.objects.filter(user=request.user, is_default=True).exclude(id=address.id).update(is_default=False)

           
            address.is_default = True
            address.save()

            messages.success(request, "Default address updated successfully!")

    return redirect('/profile#address')


from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def update_profile_image(request):
    if request.method == 'POST' and request.FILES.get('profile_image'):
        user = request.user

      
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(user=user)

        profile = user.profile
        profile.profile_image = request.FILES['profile_image']
        profile.save()

        return JsonResponse({'status': 'success', 'image_url': profile.profile_image.url})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect

@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = request.user

        if not user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('/profile?tab=password')  

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('/profile?tab=password')

        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('/profile?tab=password')

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Your password has been updated successfully.')
        return redirect('/profile?tab=password')

    return redirect('/profile?tab=password')



@never_cache
@login_required
def view_order(request, order_id):
    """View order details"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'user_panel/user_profile.html', {'order': order})
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product, Cart, Wishlist
from django.views.decorators.http import require_POST
from accounts.models import ProductVariant
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Cart, ProductVariant, Wishlist,Order,OrderItem,ReturnRequest
@never_cache
@require_POST
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('user_panel:login')

    variant_id = request.POST.get('variant_id')
    quantity = request.POST.get('quantity', 1)  
    try:
        quantity = int(quantity)
        if quantity < 1:
            quantity = 1
    except ValueError:
        quantity = 1

    if not variant_id:
        messages.error(request, "Please select a product variant.")
        return redirect('user_panel:product_detail', pk=product_id)

    variant = get_object_or_404(ProductVariant, id=variant_id)
    product = variant.product

    if product.is_blocked or not product.is_available:
        messages.error(request, "This product is currently unavailable.")
        return redirect('user_panel:product_detail', pk=product.id)

    if product.category.is_blocked or not product.category.is_available:
        messages.error(request, "This product's category is currently unavailable.")
        return redirect('user_panel:product_detail', pk=product.id)

    if variant.stock == 0:
        messages.error(request, "This product variant is out of stock.")
        return redirect('user_panel:product_detail', pk=product.id)

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product_variant=variant,
        defaults={'quantity': quantity, 'product': product}
    )

    if not created:
        new_quantity = cart_item.quantity + quantity
        if new_quantity <= variant.stock:
            cart_item.quantity = new_quantity
            cart_item.save()
            messages.success(request, "Product quantity updated in cart.")
        else:
            messages.warning(request, f"Only {variant.stock} units available in stock.")
    else:
        messages.success(request, "Product added to cart.")

    Wishlist.objects.filter(user=request.user, product=product).delete()

    return redirect('user_panel:cart')

@never_cache
@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('user_panel:cart_view') 

from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from decimal import Decimal
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from decimal import Decimal
from .utils import calculate_cart_totals
@never_cache
@login_required
def cart_view(request):
    
    cart_items = Cart.objects.filter(
        user=request.user,
        product__is_deleted=False
    ).select_related('product')

    totals = calculate_cart_totals(cart_items)

    context = {
        'cart_items': cart_items,
        'total_items': totals['total_qty'],
        'subtotal': totals['subtotal'],
        'discount': totals['coupon_discount'],
        'delivery_fee': totals['shipping'],
        'total_price': totals['subtotal'],  
        'total': totals['final_total'],
    }
    return render(request, 'user_panel/cart.html', context)
from django.db.models import Sum


def get_total_items(user):
    return Cart.objects.filter(user=user).aggregate(Sum('quantity'))['quantity__sum'] or 0

@never_cache
@require_POST
@login_required
def increment_cart(request):
    cart_id = request.POST.get('cart_id')
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    

    if cart_item.quantity < cart_item.product_variant.stock:
        cart_item.quantity += 1
        cart_item.save()
        total_items = get_total_items(request.user)

        totals = calculate_cart_totals(Cart.objects.filter(user=request.user))
        item_total = cart_item.quantity * cart_item.product_variant.price
        return JsonResponse({
            'status': 'success',
            'quantity': cart_item.quantity,
            'item_total': float(item_total),
            'subtotal': float(totals['subtotal']),
            'discount': float(totals.get('coupon_discount', 0)),
            'total': float(totals['final_total']),
            'total_items': total_items,
        })
    else:
        return JsonResponse({'status': 'max_reached', 'message': 'No more stock available'})

@never_cache
@require_POST
@login_required
def decrement_cart(request):
    cart_id = request.POST.get('cart_id')
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
        total_items = get_total_items(request.user)

        totals = calculate_cart_totals(Cart.objects.filter(user=request.user))
        item_total = cart_item.quantity * cart_item.product_variant.price
        return JsonResponse({
            'status': 'success',
            'quantity': cart_item.quantity,
            'item_total': float(item_total),
            'subtotal': float(totals['subtotal']),
            'discount': float(totals.get('coupon_discount', 0)),
            'total': float(totals['final_total']),
            'total_items': total_items,
        })
    else:
        cart_item.delete()
        return JsonResponse({'status': 'deleted', 'message': 'Item removed'})


@never_cache
@login_required
@require_POST
def remove_cart_item(request, cart_id):
    Cart.objects.filter(id=cart_id, user=request.user).delete()
    return redirect('user_panel:cart')
from decimal import Decimal
from django.db.models import F, ExpressionWrapper, DecimalField, Sum
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Cart, Address,Wallet,Wishlist
from decimal import Decimal
from django.db.models import F, Sum, ExpressionWrapper, DecimalField
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import AddressForm 
from decimal import Decimal
import razorpay
from django.conf import settings
from app.models import Coupon,Wallet  # ensure you have a Coupon model
from datetime import date
from django.db import models
@never_cache
@login_required
def checkout_view(request):
    Cart.objects.filter(user=request.user, product__is_deleted=True).delete()
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    cart_items = Cart.objects.filter(user=request.user, product__is_deleted=False).select_related('product')

    if not cart_items.exists():
        messages.warning(request, "Your cart is empty. Please add items before checkout.")
        return redirect('user_panel:cart')

    out_of_stock_items = []
    for item in cart_items:
        if item.quantity > item.product_variant.stock:
            out_of_stock_items.append(item)

    if out_of_stock_items:
        for item in out_of_stock_items:
            if item.product_variant.stock > 0:
                item.quantity = item.product_variant.stock
                item.save()
                messages.warning(request, f"Quantity for '{item.product.name}' adjusted to {item.product_variant.stock} due to stock.")
            else:
                item.delete()
                messages.warning(request, f"'{item.product.name}' removed from cart due to out of stock.")
        return redirect('user_panel:cart')
   
    # === APPLY COUPON ===
    coupon_discount = 0
    applied_coupon = None
    coupon = None

    if request.method == 'POST':
        if 'apply_coupon' in request.POST:
            code = request.POST.get('coupon_code', '').strip()
            try:
                coupon = Coupon.objects.get(code__iexact=code, active=True)
                if coupon.expiry_date and coupon.expiry_date < date.today():
                    messages.error(request, "Coupon has expired.")
                elif coupon.used_users.filter(id=request.user.id).exists():
                    messages.error(request, "You have already used this coupon.")
                else:
                    request.session['applied_coupon'] = coupon.code
                    messages.success(request, f"Coupon '{coupon.code}' applied successfully!")
                    return redirect('user_panel:checkout')

            except Coupon.DoesNotExist:
                messages.error(request, "Invalid coupon code.")
        elif 'remove_coupon' in request.POST:
            request.session.pop('applied_coupon', None)
            messages.info(request, "Coupon removed successfully.")
            return redirect('user_panel:checkout')

    # === CALCULATE TOTALS ===
    totals = calculate_cart_totals(cart_items)
    sub_total = totals.get('subtotal', 0)

    if 'applied_coupon' in request.session:
        try:
            coupon = Coupon.objects.get(code=request.session['applied_coupon'], active=True)
            applied_coupon = coupon
            if coupon.valid_from and coupon.valid_to >= date.today():
                if not coupon.used_users.filter(id=request.user.id).exists():
                    coupon_discount = (Decimal(coupon.discount_percentage) / Decimal(100)) * sub_total
                    coupon_discount = coupon_discount.quantize(Decimal('0.01'))

                    totals['grand_total'] = sub_total - coupon_discount
                else:
                    messages.warning(request, "Coupon already used. Removing.")
                    request.session.pop('applied_coupon')
            else:
                messages.warning(request, "Coupon expired. Removing.")
                request.session.pop('applied_coupon')
        except Coupon.DoesNotExist:
            request.session.pop('applied_coupon', None)
        
# 💡 Recalculate totals WITH coupon if valid
    totals = calculate_cart_totals(cart_items, coupon=coupon)

    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first()
    address_form = AddressForm()
    available_coupons = Coupon.objects.filter(
    active=True
).exclude(
    used_users=request.user
).filter(
    models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=date.today())
)


    context = {
        'cart_items': cart_items,
        'addresses': addresses,
        'default_address': default_address,
        'address_form': address_form,
        'wallet':wallet,
        'coupon_discount': coupon_discount,
        'applied_coupon': applied_coupon,
        'applied_coupon_code': applied_coupon.code if applied_coupon else '',
        'available_coupons':available_coupons,
        **totals
    }
    return render(request, 'user_panel/checkout.html', context)


@never_cache
@login_required
def add_address_checkout(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address added successfully!")
    return redirect('user_panel:checkout')



@never_cache
@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect('user_panel:wishlist')
@never_cache
@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    return redirect('user_panel:wishlist')
@never_cache
@login_required
def wishlist_view(request):
    
    Wishlist.objects.filter(user=request.user, product__is_deleted=True).delete()

   
    wishlist_items = Wishlist.objects.filter(
        user=request.user,
        product__is_deleted=False
    ).select_related('product')

    item_count = wishlist_items.count()

    context = {
        'wishlist_items': wishlist_items,
        'item_count': item_count,
    }
    return render(request, 'user_panel/wishlist.html', context)
@never_cache
@login_required
def add_to_cart_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user = request.user

   
    existing_items = Cart.objects.filter(user=user, product=product)

    if existing_items.exists():
        
        main_item = existing_items.first()
        main_item.quantity += 1
        main_item.save()

        if existing_items.count() > 1:
            for duplicate in existing_items.exclude(id=main_item.id):
                main_item.quantity += duplicate.quantity
                duplicate.delete()
            main_item.save()
    else:
       
        Cart.objects.create(user=user, product=product, quantity=1)

   
    Wishlist.objects.filter(user=user, product=product).delete()

    return redirect('user_panel:wishlist')

import uuid

def generate_order_id():
    return str(uuid.uuid4()).replace('-', '').upper()[:12]  
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from app.models import Cart, Address, Order, OrderItem,Coupon,ReturnRequest,Wallet
from app.utils import calculate_cart_totals
from django.db import transaction
from decimal import Decimal

@never_cache
@login_required
@transaction.atomic
def place_order(request):
    coupon=None
    user = request.user
    address_id = request.POST.get('address')
    use_wallet = request.POST.get('use_wallet') == 'true' 

   
    if not address_id or not address_id.isdigit():
        messages.error(request, "Please select a valid delivery address.")
        return redirect('user_panel:checkout') 
    try:
        address = Address.objects.get(id=address_id, user=user)
    except Address.DoesNotExist:
        messages.error(request, "Selected address is not available.")
        return redirect('user_panel:checkout')

    cart_items = Cart.objects.filter(user=user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('user_panel:cart')

    
    

    
    if 'applied_coupon' in request.session:
        try:
            coupon = Coupon.objects.get(code=request.session['applied_coupon'], active=True)
        except Coupon.DoesNotExist:
            coupon = None
    totals = calculate_cart_totals(cart_items, coupon=coupon)
    total_amount = Decimal(totals['final_total'])

     
    wallet_amount_used = Decimal(0)
    wallet, _ = Wallet.objects.get_or_create(user=user)

    if use_wallet and wallet.balance > 0:
        if wallet.balance >= total_amount:
            wallet_amount_used = total_amount
            wallet.balance -= total_amount
            total_amount = Decimal(0)
        else:
            wallet_amount_used = wallet.balance
            total_amount -= wallet.balance
            wallet.balance = Decimal(0)
        wallet.save()

    order = Order.objects.create(
        user=user,
        order_id=generate_order_id(),
        payment_method='COD',
        status='pending',
        subtotal=totals['subtotal'],
        discount=totals['coupon_discount'],
        shipping=totals['shipping'],
        total_amount=totals['final_total'],
        wallet_amount=wallet_amount_used,
        address_name=user.first_name or user.username,
        address_phone=getattr(user, 'mobile', ''),
        address_line1=address.street,
        address_line2='',
        address_city=address.city,
        address_state=address.state,
        address_zipcode=address.pincode,
        coupon=coupon,
    )
    if coupon:
        coupon.used_users.add(user)
        request.session.pop('applied_coupon', None) 
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product_variant=item.product_variant,
            product_name=item.product_variant.product.name,
            quantity=item.quantity,
            price=item.product_variant.price,
            subtotal=item.quantity * item.product_variant.price
        )
        item.product_variant.stock -= item.quantity
        item.product_variant.save()

    cart_items.delete()

    if total_amount == 0:
        order.status = 'pending'
        order.save()
        return redirect('user_panel:order_success', order_id=order.order_id)

    if coupon and user in coupon.used_users.all():
        messages.error(request, "Coupon already used.")
        return redirect('user_panel:checkout')


    return redirect('user_panel:order_success', order_id=order.order_id)


@never_cache
@login_required
def order_list(request):
    user = request.user
    query = request.GET.get('q')
    
    order = None

    if query:
        orders = Order.objects.filter(order_id__icontains=query, user=user)
        if orders.count() == 1:
            order = orders.first()
            orders = None
    else:
        orders = Order.objects.filter(user=user).order_by('-created_at')

    return render(request, 'user_panel/orders.html', {
        'orders': orders,
        'order': order,
        'query': query,
    })


@never_cache
@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'user_panel/order_success.html', {'order': order})


from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required

@never_cache
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return_request = ReturnRequest.objects.filter(order=order).first()
    order_items = order.items.all()
   
    all_cancelled = all(item.status == "Cancelled" for item in order_items)

    if order.status in ['processing', '', None]:
        if all_cancelled:
            order.status = 'Cancelled'
        elif any(item.status == 'Cancelled' for item in order_items):
            order.status = 'Partially Cancelled'
        else:
            order.status = "processing"
        order.save()

    # Calculate total, discount, final
    subtotal = sum(item.price * item.quantity for item in order_items)
    shipping = 40 if subtotal < 500 else 0
    coupon_discount = order.coupon.discount_percentage if order.coupon else 0
    total_discount = coupon_discount  # You can also add other discounts here
    final_price = subtotal + shipping - total_discount

    context = {
        'order': order,
        'order_items': order_items,
        'all_cancelled': all_cancelled,
        'subtotal': subtotal,
        'shipping': shipping,
        'coupon_discount': coupon_discount,
        'final_price': final_price,
        'return_request': return_request,
    }

    return render(request, 'user_panel/order_detail.html', context)





@never_cache
@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'user_panel/user_profile.html', {'orders': orders})
@never_cache
@login_required
def cancel_entire_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        for item in order.items.all():
            if item.status != 'Cancelled':
                item.status = 'Cancelled'
                item.cancel_reason = reason
                item.save()
              
                variant = item.product_variant
                variant.stock += item.quantity
                variant.save()
        order.status = 'Cancelled'
        order.save()
        messages.success(request, "Order cancelled successfully.")
        return redirect('user_panel:order_list')

    return render(request, 'user_panel/cancel_order.html', {'order': order})

@never_cache
@login_required
def cancel_order_item(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)

    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        if item.status != 'Cancelled':
          
            item.status = 'Cancelled'
            item.cancel_reason = reason
            item.save()

          
            item.product_variant.stock += item.quantity
            item.product_variant.save()

         
            order = item.order
            items = order.items.all()
            cancelled = items.filter(status='Cancelled').count()

            if cancelled == items.count():
                order.status = 'Cancelled'
            elif cancelled > 0:
                order.status = 'processing'  
            else:
                order.status = 'Pending'

            order.save()

            messages.success(request, "Item cancelled successfully.")

        return redirect('user_panel:order_detail', order_id=item.order.order_id)

    return render(request, 'user_panel/cancel_item.html', {'item': item})




@never_cache
@login_required
def return_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

  
    existing_return = ReturnRequest.objects.filter(order=order).exists()
    if order.status != 'delivered' or existing_return:
        messages.warning(request, "This order is  not delivered/already filed the complaints.")
        return redirect('user_panel:order_list')

    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        refund_amount = order.total_amount

       
        ReturnRequest.objects.create(
            user=request.user,
            order=order,
            reason=reason,
            refund_amount=refund_amount,
        )

   
        for item in order.items.all():
            if item.status == 'Delivered':
                item.status = 'Returned'
                item.save()
                item.product_variant.stock += item.quantity
                item.product_variant.save()

     
        order.status = 'returned'
        order.return_status = 'requested'
        order.save()

        messages.success(request, "Complaint submitted successfully.")
        return redirect('user_panel:order_list')

    return render(request, 'user_panel/return_order.html', {'order': order})

from django.http import HttpResponse
from .pdf_invoice import generate_invoice_pdf


def download_invoice(request, order_id):
    order = Order.objects.get(order_id=order_id, user=request.user)
    pdf = generate_invoice_pdf('user_panel/invoice_template.html', {'order': order})

    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{order_id}.pdf"'
        return response
    return HttpResponse("Failed to generate invoice", status=400)
from django.db.models.signals import post_save
from django.dispatch import receiver
from .forms import ReturnRequestForm
@receiver(post_save, sender=CustomUser)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)

@login_required

def request_return(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    if ReturnRequest.objects.filter(order=order).exists():
        messages.warning(request, "You have already requested a return for this order.")
        return redirect('user_panel:order_list')

    if order.status != 'delivered':
        messages.warning(request, "Only delivered orders can be returned.")
        return redirect('user_panel:order_list')

    if request.method == 'POST':
        form = ReturnRequestForm(request.POST, request.FILES)
        if form.is_valid():
            return_request = form.save(commit=False)
            return_request.user = request.user
            return_request.order = order
            return_request.refund_amount = order.total_amount
            return_request.save()

     
            for item in order.items.all():
                if item.status == 'Delivered':
                    item.status = 'Returned'
                    item.save()
                    item.product_variant.stock += item.quantity
                    item.product_variant.save()

            order.status = 'returned'
            order.return_status = 'requested'
            order.save()

            messages.success(request, "Return request submitted.")
            return redirect('user_panel:order_list')
    else:
        form = ReturnRequestForm()

    return render(request, 'user_panel/return_request_form.html', {'form': form, 'order': order})
from .models import WalletTransaction
@login_required
def wallet_view(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)

 
    transactions = WalletTransaction.objects.filter(wallet__user=request.user).order_by('-created_at')

    return_requests = ReturnRequest.objects.filter(user=request.user, refunded=True).order_by('-requested_at')

    return render(request, 'user_panel/wallet.html', {
        'wallet': wallet,
        'transactions': transactions,
        'return_requests': return_requests,
    })






from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseBadRequest
from django.conf import settings
import razorpay
from .models import Order, Payment  # Adjust if model path differs
import logging

logger = logging.getLogger(__name__)  # Enable logging


@login_required
def order_payment_success(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'user_panel/order_payment_success.html', {'order': order})

def payment_failed(request):
    return render(request, 'user_panel/payment_failed.html')







from django.urls import reverse




from decimal import Decimal
from django.db import transaction

from .utils import calculate_cart_totals  # Assuming you have this function
from django.utils.crypto import get_random_string

@transaction.atomic
@login_required
def razorpay_checkout_view(request):
    address_id = request.POST.get('address')
    use_wallet = request.POST.get('use_wallet') == 'true'
  
    if not address_id or not address_id.isdigit():
        messages.error(request, "Please select a valid delivery address.")
        return redirect('user_panel:checkout')

    try:
        address = Address.objects.get(id=address_id, user=request.user)
    except Address.DoesNotExist:
        messages.error(request, "Selected address is not available.")
        return redirect('user_panel:checkout')

    # Store in session so payment_handler can also access it if needed
    request.session['checkout_address_id'] = address.id
    coupon_code = request.session.get('applied_coupon')
    
    coupon = None
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, active=True)
        except Coupon.DoesNotExist:
            coupon = None

    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('user_panel:cart')

    # Step 2: Calculate totals
    totals = calculate_cart_totals(cart_items, coupon=coupon)
    total_amount = Decimal(totals['final_total'])

    if total_amount < 1:
        messages.error(request, "Order amount must be at least ₹1.")
        return redirect('user_panel:cart')
    
    wallet_amount_used = Decimal(0)
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if use_wallet and wallet.balance > 0:
        if wallet.balance >= total_amount:
            wallet_amount_used = total_amount
            wallet.balance -= total_amount
            total_amount = Decimal(0)
        else:
            wallet_amount_used = wallet.balance
            total_amount -= wallet.balance
            wallet.balance = Decimal(0)
        wallet.save()

    if total_amount == 0:
        order = Order.objects.create(
            user=request.user,
            order_id=get_random_string(12).upper(),
            total_amount=wallet_amount_used,
            wallet_amount=wallet_amount_used,
            status='placed',
            payment_status='Paid',
            payment_method='Wallet',
            subtotal=totals['subtotal'],
            shipping=totals['shipping'],
            discount=totals['coupon_discount'],
            address_name=request.user.first_name or request.user.username,
            address_phone=getattr(request.user, 'mobile', ''),
            address_line1=address.street,
            address_line2='',
            address_city=address.city,
            address_state=address.state,
            address_zipcode=address.pincode,
        )

        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_variant=cart_item.product_variant,
                product_name=cart_item.product.name,
                quantity=cart_item.quantity,
                price=cart_item.get_price(),
                subtotal=cart_item.total_price()
            )

        cart_items.delete()
        return redirect('user_panel:order_success')


    # Step 3: Create Razorpay order
    amount_paise = int(total_amount * 100)
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        razorpay_order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1
        })
    except razorpay.errors.BadRequestError as e:
        messages.error(request, f"Payment error: {str(e)}")
        return redirect('user_panel:cart')

     
    order = Order.objects.create(
            user=request.user,
            order_id=get_random_string(12).upper(),
            razorpay_order_id=razorpay_order['id'],
            total_amount=total_amount+wallet_amount_used,
            wallet_amount=wallet_amount_used,
            status='pending',
            payment_method='Online',
            subtotal=totals['subtotal'],
            shipping=totals['shipping'],
            discount=totals['coupon_discount'],
           
            address_name=request.user.first_name or request.user.username,
            address_phone=getattr(request.user, 'mobile', ''),
            address_line1=address.street,
            address_line2='',
            address_city=address.city,
            address_state=address.state,
            address_zipcode=address.pincode,
            )

    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            product_variant=cart_item.product_variant,
            product_name=cart_item.product.name,
            quantity=cart_item.quantity,
            price=cart_item.get_price(),
            subtotal=cart_item.total_price()
        )

    # Clear cart
   

    context = {
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'amount': amount_paise,
        'order': order,
        'callback_url': '/payment/handler/',
        'totals': totals,
        'address_id': request.session.get('checkout_address_id'),
    }

    return render(request, 'user_panel/razorpay_checkout.html', context)

    # Fallback if method != POST
    return redirect('user_panel:cart')

import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponseBadRequest
from app.models import Order,Payment

@csrf_exempt
def payment_handler(request):
    if request.method != "POST":
        return HttpResponseBadRequest()

    payment_id = request.POST.get('razorpay_payment_id')
    order_id = request.POST.get('razorpay_order_id')
    signature = request.POST.get('razorpay_signature')

    order_obj = Order.objects.filter(razorpay_order_id=order_id).first()
    if not order_obj:
        print("❌ Order not found for Razorpay ID:", order_id)
        return redirect('user_panel:payment_failed')

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    try:
        if not payment_id:
            # No payment attempt → fail, but keep cart intact
            order_obj.payment_status = "Failed"
            order_obj.status = "pending"
            order_obj.save()
            return redirect('user_panel:payment_failed')

        # Verify signature
        params_dict = {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': order_id,
            'razorpay_signature': signature
        }
        client.utility.verify_payment_signature(params_dict)

        # Fetch payment from Razorpay
        payment_details = client.payment.fetch(payment_id)
        print("🔍 Razorpay Payment Details:", payment_details)

        if payment_details['status'] != "captured":
            order_obj.payment_status = "Failed"
            order_obj.status = "pending"
            order_obj.save()
            return redirect('user_panel:payment_failed')

        # ✅ Payment success
        order_obj.razorpay_payment_id = payment_id
        order_obj.razorpay_signature = signature
        order_obj.payment_status = "Paid"
        order_obj.status = "placed"
        order_obj.save()

        # Clear cart only on success
        Cart.objects.filter(user=order_obj.user).delete()

        return redirect('user_panel:order_success', order_id=order_obj.order_id)

    except razorpay.errors.SignatureVerificationError:
        order_obj.payment_status = "Failed"
        order_obj.status = "pending"
        order_obj.save()
        return redirect('user_panel:payment_failed')

    except Exception as e:
        print("Payment error:", str(e))
        order_obj.payment_status = "Failed"
        order_obj.status = "pending"
        order_obj.save()
        return redirect('user_panel:payment_failed')




from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib import messages
from .models import Cart, Coupon
from .utils import calculate_cart_totals  # Assuming this is your utility function
import json

@csrf_exempt
def apply_coupon(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            code = data.get('coupon_code', '').strip()

            cart_items = Cart.objects.filter(user=request.user).select_related('product_variant__product')

            try:
                coupon = Coupon.objects.get(code__iexact=code, active=True)
            except Coupon.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid coupon code.'})

            # Apply coupon to totals
            

            # Save coupon to session
            request.session['applied_coupon'] = coupon.code
            totals = calculate_cart_totals(cart_items, coupon=coupon)

            return JsonResponse({
                'success': True,
                'coupon_discount': f"{totals['coupon_discount']:.2f}",
                'subtotal': f"{totals['subtotal']:.2f}",
                'final_total': f"{totals['final_total']:.2f}",
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Server error: {str(e)}'})
from django.http import JsonResponse
from .models import Cart, ProductVariant

def get_cart_items(user):
    return Cart.objects.filter(user=user)

def calculate_cart_subtotal(cart_items):
    return sum(item.quantity * item.product_variant.price for item in cart_items)

def calculate_shipping(subtotal):
    return 0 if subtotal >= 500 else 50  # Example: free shipping for orders >= ₹500


@csrf_exempt
def remove_coupon(request):
    if request.method == 'POST':
        request.session.pop('applied_coupon', None)

        cart_items = Cart.objects.filter(user=request.user).select_related('product_variant__product')
        from .utils import calculate_cart_totals
        totals = calculate_cart_totals(cart_items)

        return JsonResponse({
            'success': True,
            'message': 'Coupon removed successfully.',
            'coupon_discount': f"{totals['coupon_discount']:.2f}",
            'subtotal': f"{totals['subtotal']:.2f}",
            'final_total': f"{totals['final_total']:.2f}",
        })

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


