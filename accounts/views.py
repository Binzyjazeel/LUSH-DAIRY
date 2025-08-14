
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import CustomUser 
from django.core.paginator import Paginator
from django.db.models import Q 
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import Category
from .forms import CategoryForm
from .models import Product,ProductImage
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test


@never_cache
def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_panel:admin_dashboard')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            print("Logged in successfully as superuser")
            login(request, user)
            return redirect('admin_panel:admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not an admin user')

    
    response = render(request, 'admin_panel/login.html')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def admin_logout(request):
    logout(request)
    return redirect('admin_panel:admin_login')

@never_cache
@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('admin_panel:admin_login')

    

    response = render(request, 'admin_panel/dashboard.html')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@never_cache
@login_required
def user_list(request):
    query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)

    
    users = CustomUser.objects.filter(
        Q(username__icontains=query) | Q(email__icontains=query) |
        Q(first_name__icontains=query) | Q(last_name__icontains=query)
    ).order_by('-created_at')  
    

  
    paginator = Paginator(users, 10) 
    page_obj = paginator.get_page(page_number)

    context = {
        'query': query,
        'page_obj': page_obj,
    }
    return render(request, 'admin_panel/user_list.html', context)

@require_POST
def toggle_block_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_blocked = not user.is_blocked
    user.save()
    messages.success(request, f"User {'blocked' if user.is_blocked else 'unblocked'} successfully.")
    return redirect('admin_panel:user_list')


def category_list(request):
    search_query = request.GET.get('search', '')
    categories = Category.objects.filter(is_deleted=False)

    if search_query:
        categories = categories.filter(name__icontains=search_query)

    categories = categories.order_by('-created_at')  

    paginator = Paginator(categories, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_panel/category_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
    })

def category_add(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category added successfully.")
            return redirect('admin_panel:category_list')
    else:
        form = CategoryForm()
    return render(request, 'admin_panel/category_form.html', {'form': form})

def category_edit(request, pk):
    
    category = get_object_or_404(Category, pk=pk, is_deleted=False)

   
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        print("🔍 POST data received:", request.POST)

        if form.is_valid():
            if form.has_changed():
                print("✅ Form is valid and has changes:", form.changed_data)
                form.save()
                messages.success(request, "Category updated successfully.")
            else:
                print("⚠️ Form submitted but no changes detected.")
                messages.info(request, "No changes were made to the category.")
            return redirect('admin_panel:category_list')
        else:
            print("❌ Form is invalid:", form.errors)

    else:
        
        form = CategoryForm(instance=category)

   
    return render(request, 'admin_panel/edit_category.html', {'form': form})

def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, is_deleted=False)
    category.is_deleted = True 
    category.save()
    messages.success(request, "Category deleted successfully.")
    return redirect('admin_panel:category_list')

def category_clear_search(request):
    return redirect('admin_panel:category_list')




from .forms import ProductForm

def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        images = request.FILES.getlist('images') 

        if form.is_valid():
            if len(images) < 3:
                messages.error(request, "Please upload at least 3 images.")
            else:
                product = form.save()
                for image in images:
                    ProductImage.objects.create(product=product, image=image)
                messages.success(request, "Product added successfully.")
        
                return redirect('product_list')
        else:
            messages.error(request, "Form is not valid.")
    else:
        form = ProductForm()

    return render(request, 'admin_panel/add_product.html', {'form': form})

    



def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_deleted=False)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            for file in request.FILES.getlist('images'):
                ProductImage.objects.create(product=product, image=file)
            messages.success(request, "Product updated successfully.")
            return redirect('admin_panel:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'admin_panel/edit_product.html', {'form': form, 'product': product})


def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_deleted = True
    product.save()
    messages.success(request, "Product deleted (soft delete).")
    return redirect('admin_panel:product_list')

def product_list(request):
    query = request.GET.get('q')
    products = Product.objects.filter(is_deleted=False)
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    paginator = Paginator(products, 6)  # 6 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'admin_panel/product_list.html', context)
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import io
from PIL import Image

@csrf_exempt
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('cropped_image'):
        product_id = request.POST.get('product_id')
        if not product_id:
            return JsonResponse({'status': 'error', 'message': 'Missing product ID'})

        product = get_object_or_404(Product, id=product_id)

        cropped_image = request.FILES['cropped_image']

        img = Image.open(cropped_image)
        img = img.resize((400, 400))

        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)

        final_img = InMemoryUploadedFile(
            buffer, None, f'cropped_{timezone.now().timestamp()}.jpg',
            'image/jpeg', buffer.tell(), None
        )

       
        ProductImage.objects.create(product=product, image=final_img)

        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'No image received'})

from .forms import ProductVariantForm
from .models import ProductVariant
from app.models import Order,OrderItem,ReturnRequest

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from .models import Product, ProductVariant
from .forms import ProductVariantForm
from django.urls import reverse

def add_variant(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductVariantForm(request.POST)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.product = product
            variant.save()
            messages.success(request, "Variant added successfully.")
            return redirect('admin_panel:manage_variants', product_id=product.id)
       
    else:
        form = ProductVariantForm(initial={'product': product})

    return render(request, 'admin_panel/add_variant.html', {'form': form, 'product': product})







from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from app.models import Order,OrderItem,ReturnRequest 





def admin_order_list(request):
    orders = Order.objects.all()

    query = request.GET.get('q')
    status_filter = request.GET.get('status', 'all')
    sort_by = request.GET.get('sort', 'date_desc')

    if query:
        orders = orders.filter(
            Q(order_id__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query)
        )

    if status_filter and status_filter != 'all':
        orders = orders.filter(status=status_filter)

    if sort_by == 'date_asc':
        orders = orders.order_by('created_at')
    elif sort_by == 'date_desc':
        orders = orders.order_by('-created_at')
    elif sort_by == 'amount_asc':
        orders = orders.order_by('total_amount')
    elif sort_by == 'amount_desc':
        orders = orders.order_by('-total_amount')

    paginator = Paginator(orders, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    status_choices = [
        {'key': 'all', 'val': 'All Status'},
        {'key': 'pending', 'val': 'Order Placed'},
        {'key': 'shipped', 'val': 'Shipped'},
        {'key': 'delivered', 'val': 'Delivered'},
        {'key': 'cancelled', 'val': 'Cancelled'},
    ]

    sort_choices = [
        {'key': 'date_desc', 'val': 'Date (Newest)'},
        {'key': 'date_asc', 'val': 'Date (Oldest)'},
        {'key': 'amount_desc', 'val': 'Amount (High to Low)'},
        {'key': 'amount_asc', 'val': 'Amount (Low to High)'},
    ]

    stats_list = [
        {'label': 'Total Orders', 'count': Order.objects.count(), 'color': 'primary'},
        {'label': 'Pending Orders', 'count': Order.objects.filter(status='pending').count(), 'color': 'warning'},
        {'label': 'Delivered Orders', 'count': Order.objects.filter(status='delivered').count(), 'color': 'success'},
        {'label': 'Return Requests', 'count': Order.objects.filter(returnrequest__isnull=False).count(), 'color': 'danger'},
    ]

    context = {
        'orders': page_obj,
        'query': query,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'status_choices': status_choices,
        'sort_choices': sort_choices,
        'stats_list': stats_list,
    }

    return render(request, 'admin_panel/order.html', context)


from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages


def admin_change_order_status(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.ORDER_STATUS_CHOICES).keys():
            order.status = new_status
            order.save()
            messages.success(request, f"Order {order_id} status updated to {new_status}.")
        else:
            messages.error(request, "Invalid status selected.")

        return redirect('admin_panel:admin_order_detail', order_id=order_id)

    return render(request, 'admin_panel/change_order_status.html', {'order': order})

   
def admin_verify_return_request(request, return_id):
    return_request = get_object_or_404(ReturnRequest, id=return_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept':
            return_request.verified = True
            return_request.save()

            
            user_wallet = return_request.user.wallet
            user_wallet.balance += return_request.refund_amount
            user_wallet.save()

            messages.success(request, f"Return request accepted and ₹{return_request.refund_amount} refunded to wallet.")
        elif action == 'reject':
            return_request.verified = False
            return_request.save()
            messages.info(request, "Return request rejected.")

        return redirect('admin_panel:admin_return_requests')

    return render(request, 'admin_panel/verify_return.html', {'return_request': return_request})

def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    return render(request, 'admin_panel/order_details.html', {'order': order})


def inventory_list(request):
    query = request.GET.get('q')
    if query:
        products = Product.objects.filter(name__icontains=query).prefetch_related('variants')
    else:
        products = Product.objects.all().prefetch_related('variants')
    return render(request, 'admin_panel/inventory_list.html', {'products': products})

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import ProductVariant


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import ProductVariant

def update_stock(request, variant_id):
    if request.method == 'POST':
        stock = request.POST.get('stock')
        if stock is None:
            messages.error(request, "Stock value is required.")
            return redirect('admin_panel:inventory_list')
        try:
            stock = int(stock)
            variant = get_object_or_404(ProductVariant, id=variant_id)
            variant.stock = stock
            variant.save()
            messages.success(request, f'Stock for variant \"{variant.variant_name}\" updated successfully.')
        except ValueError:
            messages.error(request, "Invalid stock value.")
    return redirect('admin_panel:inventory_list')

def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Order.ORDER_STATUS).keys():
            order.status = status
            order.save()
            return redirect('admin_panel:admin_order_detail', order_id=order_id)

    context = {
        'order': order,
        'status_choices': Order.ORDER_STATUS,
    }
    return render(request, 'admin_panel/order_details.html', context)



from django.shortcuts import get_object_or_404, redirect, render
from .models import ProductVariant
from .forms import ProductVariantForm

def edit_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product = variant.product

    if request.method == 'POST':
        form = ProductVariantForm(request.POST, instance=variant)
        if form.is_valid():
            form.save()
            return redirect('admin_panel:manage_variants', product_id=product.id)
    else:
        form = ProductVariantForm(instance=variant)

    return render(request, 'admin_panel/edit_variant.html', {
        'form': form,
        'product': product,
        'title': 'Edit'
    })


def delete_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product_id = variant.product.id
    variant.delete()
    messages.success(request, "Variant deleted successfully.")
    return redirect('admin_panel:manage_variants', product_id=product_id)


def manage_variants(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variants = product.variants.all()
    return render(request, 'admin_panel/manage_variants.html', {
        'product': product,
        'variants': variants,
    })

from app.models import ReturnRequest, Wallet
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
@login_required


def approve_return_request(request, request_id):
    return_request = get_object_or_404(ReturnRequest, id=request_id)
    order = return_request.order

    
    if not return_request.verified:
        return_request.verified = True
        messages.info(request, "Complaint verified.")

    
    if not return_request.refunded:
        wallet, _ = Wallet.objects.get_or_create(user=return_request.user)
        wallet.credit(return_request.refund_amount)
        return_request.refunded = True
        messages.success(request, f"₹{return_request.refund_amount} refunded to wallet.")

    
    if order.status != 'returned' or order.return_status != 'approved':
        order.status = 'returned'
        order.return_status = 'approved'
        messages.info(request, "Complaint processed and fixed.")

  
    return_request.save()
    order.save()

    return redirect('admin_panel:admin_return_requests')
@login_required

def reject_return_request(request, request_id):
    return_request = get_object_or_404(ReturnRequest, id=request_id)
    order = return_request.order

    if not return_request.verified:
        return_request.verified = True  # Mark complaint verified even if rejected
        messages.info(request, "Complaint verified and rejected.")

    if not return_request.refunded:
        return_request.refund_amount = 0  # No refund
        return_request.refunded = False
        messages.warning(request, "No refund will be issued for this complaint.")

    order.return_status = 'rejected'  # Mark complaint rejected in order
    # Optionally update order.status if needed, e.g. leave as is or mark differently

    return_request.save()
    order.save()

    return redirect('admin_panel:admin_return_requests')



from django.db.models import Q
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import render, get_object_or_404
from app.models import ReturnRequest


def admin_return_requests(request):
    query = request.GET.get('q', '').strip()
    
    
    return_requests = ReturnRequest.objects.select_related('user', 'order')

   
    if query:
        return_requests = return_requests.filter(
            Q(user__email__icontains=query) |
            Q(order__order_id__icontains=query)
        )

   
    return_requests = return_requests.order_by('-requested_at')

    return render(request, 'admin_panel/return_request.html', {
        'return_requests': return_requests,
        'q': query
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from app.models import Coupon
from django.utils import timezone
from django.contrib import messages
from .forms import CouponForm

from django.core.paginator import Paginator

def coupon_list_view(request):
    User = get_user_model()
    coupons = Coupon.objects.all().order_by('-id')

    # Optional: implement search
    query = request.GET.get('q')
    if query:
        coupons = coupons.filter(code__icontains=query)

    paginator = Paginator(coupons, 6)  # 10 coupons per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,       # This is what the template expects
        'users': User.objects.all(),
        'today': timezone.now().date()
    }
    return render(request, 'admin_panel/coupon_list.html', context)

from django.utils.dateparse import parse_date

def create_coupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save()
            
            print(f"Saved Coupon: {coupon.code}, ID: {coupon.id}")  # Debug print
            messages.success(request, "Coupon created successfully!")
            return redirect('admin_panel:coupon_list')
        else:
            print(form.errors)  # Debugging
            messages.error(request, "Please correct the errors below.")
    else:
        form = CouponForm()
    return render(request, 'admin_panel/create_coupon.html', {'form': form, 'action': 'Create'})


def delete_coupon_view(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    messages.success(request, "Coupon deleted.")
    return redirect('admin_panel:coupon_list')

def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            coupon = form.save(commit=False)
            form.save()
            form.save_m2m() 
            return redirect('admin_panel:coupon_list')  # or your custom success URL
    else:
        form = CouponForm(instance=coupon)
    
    return render(request, 'admin_panel/edit_coupon.html', {'form': form, 'coupon': coupon})

from django.db.models import Sum, Count
from django.utils import timezone
from django.shortcuts import render
from app.models import Order
from datetime import datetime, timedelta


from django.db.models import Sum, Count, F


from django.utils.timezone import now

from django.shortcuts import render
from django.utils.timezone import now
from datetime import datetime, timedelta
from django.db.models import Count, Sum
from app.models import Order

def sales_report(request):
    period = request.GET.get('period', 'day')  # day, week, month, year, custom
    from_date = request.GET.get('start_date')
    to_date = request.GET.get('end_date')
    status_filter = request.GET.get('status', '')  # optional status filter

    today = now().date()

    # Start with all orders
    all_orders = Order.objects.all()
    # Delivered/completed orders only for main stats
    orders = Order.objects.all()
    statuses = [status[0] for status in Order.ORDER_STATUS]

    # Apply status filter if provided (overrides 'Delivered' filter if needed)
    if status_filter:
        orders = orders.filter(status=status_filter)
        all_orders = all_orders.filter(status=status_filter)

    # Filter by date range
    if period == 'custom' and from_date and to_date:
        try:
            start_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(to_date, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date__range=[start_date, end_date])
            all_orders = all_orders.filter(created_at__date__range=[start_date, end_date])
        except ValueError:
            # Invalid date format, ignore filter or handle error
            pass
    else:
        # Use period-based filtering
        if period == 'day':
            orders = orders.filter(created_at__date=today)
            all_orders = all_orders.filter(created_at__date=today)

        elif period == 'week':
            start_week = today - timedelta(days=7)
            orders = orders.filter(created_at__date__range=[start_week, today])
            all_orders = all_orders.filter(created_at__date__range=[start_week, today])

        elif period == 'month':
            start_month = today - timedelta(days=30)
            orders = orders.filter(created_at__date__range=[start_month, today])
            all_orders = all_orders.filter(created_at__date__range=[start_month, today])

        elif period == 'year':
            start_year = today - timedelta(days=365)
            orders = orders.filter(created_at__date__range=[start_year, today])
            all_orders = all_orders.filter(created_at__date__range=[start_year, today])

    # Aggregations on filtered 'orders' (completed/delivered)
    aggregated_data = orders.aggregate(
        total_orders=Count('id'),
        total_sales=Sum('total_amount'),  # change 'total_amount' to your field
        total_discount=Sum('discount')     # change 'discount' to your field
    )
    aggregated_data = {
    key: value if value is not None else 0
    for key, value in aggregated_data.items()
}

    # Group by status for all filtered orders
    status_summary = (
        all_orders
        .values('status')
        .annotate(
            total_orders=Count('id'),
            total_revenue=Sum('total_amount'),
            total_discount=Sum('discount')
        )
        .order_by('status')
    )

    context = {
        'aggregated_data': aggregated_data,
        'status_summary': status_summary,
        'filter_type': period,
        'start_date': from_date,
        'end_date': to_date,
        'selected_status': status_filter,
        'statuses': statuses,
    }

    return render(request, 'admin_panel/sales_report.html', context)



from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from app.models import Order  # make sure this is correct
from django.http import HttpResponse

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from datetime import datetime
from django.utils.timezone import make_aware



def download_sales_report_pdf(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    period = request.GET.get('period')

    orders = Order.objects.all()
    today = timezone.now()

    # Filtering
    if period:
        if period == 'day':
            orders = orders.filter(created_at__date=today.date())
        elif period == 'week':
            week_ago = today - timedelta(days=7)
            orders = orders.filter(created_at__gte=week_ago)
        elif period == 'month':
            orders = orders.filter(created_at__month=today.month, created_at__year=today.year)
        elif period == 'year':
            orders = orders.filter(created_at__year=today.year)

    elif start_date and end_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Make them timezone-aware
            start_date_aware = make_aware(datetime.combine(start_date_obj, datetime.min.time()))
            end_date_aware = make_aware(datetime.combine(end_date_obj, datetime.max.time()))

            orders = orders.filter(created_at__range=[start_date_aware, end_date_aware])
        except ValueError:
         pass 

# Filtering
   

    total_orders = orders.count()
    total_sales = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_discount = orders.aggregate(Sum('discount'))['discount__sum'] or 0

    # PDF setup with margins
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterTitle', alignment=1, fontSize=16, spaceAfter=10, fontName='Helvetica-Bold'))

    elements = []

    # Title
    elements.append(Paragraph(" Sales Report", styles['CenterTitle']))
    elements.append(Spacer(1, 12))

    # Summary Table
    summary_data = [
        ["Total Orders", f"{total_orders}"],
        ["Total Sales", f"Rs. {total_sales:,.2f}"],
        ["Total Discount", f"Rs. {total_discount:,.2f}"]
    ]
    summary_table = Table(summary_data, colWidths=[200, 200])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Orders Table
    order_data = [["Order ID", "User", "Amount", "Discount", "Date"]]
    for order in orders:
        order_data.append([
            f"#{order.id}",
            order.user.username,
            f"Rs. {order.total_amount:,.2f}",
            f"Rs. {order.discount:,.2f}",
            order.created_at.strftime('%Y-%m-%d')
        ])

    order_table = Table(order_data, colWidths=[70, 120, 80, 80, 100])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (2, 1), (3, -1), 'RIGHT'),  # Align currency to right
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
    ]))

    elements.append(order_table)

    # Build PDF
    doc.build(elements)
    return response
    # Build PDF
    
from openpyxl import Workbook
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from app.models import Order
from django.http import HttpResponse

def download_sales_report_excel(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    period = request.GET.get('period')

    orders = Order.objects.all()
    today = timezone.now()

    if period:
        if period == 'day':
            orders = orders.filter(created_at__date=today.date())
        elif period == 'week':
            week_ago = today - timedelta(days=7)
            orders = orders.filter(created_at__date__gte=week_ago)
        elif period == 'month':
            orders = orders.filter(created_at__month=today.month, created_at__year=today.year)
        elif period == 'year':
            orders = orders.filter(created_at__year=today.year)
    elif start_date and end_date:
        orders = orders.filter(created_at__date__range=[start_date, end_date])

    total_orders = orders.count()
    total_sales = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_discount = orders.aggregate(Sum('discount'))['discount__sum'] or 0

    wb = Workbook()
    ws = wb.active
    ws.title = "Sales Report"

    # Header row
    ws.append(["Order ID", "User", "Amount", "Discount", "Date"])

    # Data rows
    for order in orders:
        ws.append([
            order.id,
            order.user.username,
            order.total_amount,
            order.discount,
            order.created_at.strftime('%Y-%m-%d'),
        ])

    # Summary rows
    ws.append([])
    ws.append(["Total Orders", total_orders])
    ws.append(["Total Sales", total_sales])
    ws.append(["Total Discount", total_discount])

    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="sales_report.xlsx"'
    wb.save(response)
    return response


# admin_panel/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Offer
from .forms import OfferForm

def offer_list(request):
    query = request.GET.get('q', '')
    offers = Offer.objects.all()
    if query:
        offers = offers.filter(name__icontains=query)

    paginator = Paginator(offers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_panel/offer_list.html', {
        'page_obj': page_obj,
        'query': query,
        'today': timezone.now().date()
    })

def create_offer(request):
    if request.method == 'POST':
        form = OfferForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_panel:offer_list')
    else:
        form = OfferForm()
    return render(request, 'admin_panel/offer_form.html', {'form': form, 'title': 'Create Offer'})

def edit_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    if request.method == 'POST':
        form = OfferForm(request.POST, instance=offer)
        if form.is_valid():
            form.save()
            return redirect('admin_panel:offer_list')
    else:
        form = OfferForm(instance=offer)
    return render(request, 'admin_panel/offer_form.html', {'form': form, 'title': 'Edit Offer'})

def delete_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    offer.delete()
    return redirect('admin_panel:offer_list')

