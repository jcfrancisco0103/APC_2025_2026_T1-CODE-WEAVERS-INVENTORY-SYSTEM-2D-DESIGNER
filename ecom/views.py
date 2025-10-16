from django.shortcuts import render,redirect,reverse,get_object_or_404
import decimal
from . import forms,models
from django.http import HttpResponseRedirect,HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.utils import timezone
from .models import Customer, SavedAddress
from django.urls import reverse
from .forms import InventoryForm
from .forms import CustomerLoginForm
from .models import Product
from .models import InventoryItem
from .models import Orders
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods, require_GET
import requests
import json
import base64
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.http import JsonResponse

# Admin status verification endpoint for client-side security
@require_http_methods(["GET"])
def verify_admin_status(request):
    """
    AJAX endpoint to verify if current user has admin privileges
    Used by client-side security validation
    """
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        is_admin_user = is_admin(request.user)
        return JsonResponse({
            'is_admin': is_admin_user,
            'is_authenticated': request.user.is_authenticated
        })
    else:
        # Non-AJAX requests get redirected
        return redirect('adminlogin')

from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime
from decimal import Decimal

# Helper function to check if user is admin
def is_admin(user):
    """
    Check if the user has admin privileges
    """
    return user.is_authenticated and user.is_staff

# Admin required decorator
def admin_required(view_func):
    """
    Decorator that ensures only authenticated admin users can access a view.
    If user is not admin, logs them out and redirects to admin login.
    """
    def wrapper(request, *args, **kwargs):
        if not is_admin(request.user):
            # Log out the user if they're not an admin
            from django.contrib.auth import logout
            logout(request)
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('adminlogin')
        return view_func(request, *args, **kwargs)
    return wrapper

@admin_required
def user_profile_page(request, user_id):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"User profile page requested for user_id: {user_id}")

    try:
        customer = Customer.objects.get(user_id=user_id)
        logger.info(f"Customer found: {customer.user.get_full_name()} with user_id: {user_id}")
    except Customer.DoesNotExist:
        logger.error(f"Customer not found for user_id: {user_id}")
        from django.contrib import messages
        messages.error(request, 'User profile not found.')
        return redirect('admin-view-users')

    orders = Orders.objects.filter(customer=customer).order_by('-order_date')[:20]

    transactions = []
    for order in orders:
        order_items = order.orderitem_set.all()
        total_price = sum([item.price * item.quantity for item in order_items])
        # Get first product name for display, or show multiple if needed
        product_names = [item.product.name for item in order_items]
        product_name = ', '.join(product_names) if product_names else 'No products'
        transactions.append({
            'product_name': product_name,
            'order_date': order.order_date.strftime('%Y-%m-%d %H:%M') if order.order_date else '',
            'order_ref': order.order_ref or '',
            'amount': total_price,
            'status': order.status,
        })

    context = {
        'customer': customer,
        'transactions': transactions,
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'ecom/user_profile_page_partial.html', context)
    else:
        return render(request, 'ecom/user_profile_page.html', context)


@admin_required
def get_transactions_by_month(request):
    month = request.GET.get('month')
    year = request.GET.get('year')
    if not month or not year:
        return JsonResponse({'error': 'Month and year parameters are required'}, status=400)
    try:
        month = int(month)
        year = int(year)
    except ValueError:
        return JsonResponse({'error': 'Invalid month or year'}, status=400)

    # Filter orders by delivered status and month/year
    orders = models.Orders.objects.filter(
        status='Delivered',
        created_at__year=year,
        created_at__month=month
    ).order_by('-created_at')

    transactions = []
    for order in orders:
        order_items = order.orderitem_set.all()
        if not order_items.exists():
            continue
        
        total_amount = sum(float(item.price) * item.quantity for item in order_items)
        transactions.append({
            'user_name': order.customer.user.username if order.customer and order.customer.user else 'Unknown',
            'order_id': order.order_ref or '',
            'date': order.created_at.strftime('%Y-%m-%d'),
            'amount': total_amount,
            'type': 'credit' if order.status == 'Delivered' else 'debit',
        })

    return JsonResponse({'transactions': transactions})

def order_counts(request):
    if request.user.is_authenticated and is_customer(request.user):
        customer = models.Customer.objects.get(user_id=request.user.id)
        context = {
            'pending_count': models.Orders.objects.filter(customer=customer, status='Pending').count(),
            'to_ship_count': models.Orders.objects.filter(customer=customer, status='Processing').count(),
            'to_receive_count': models.Orders.objects.filter(customer=customer, status='Shipping').count(),
            'delivered_count': models.Orders.objects.filter(customer=customer, status='Delivered').count(),
            'cancelled_count': models.Orders.objects.filter(customer=customer, status='Cancelled').count(),
        }
        return context
    return {}


@login_required(login_url='customerlogin')
def home_view(request):
    products = models.Product.objects.all()
    
    # Cart count logic
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0
    
    # If user is authenticated, redirect to appropriate dashboard
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    
    # Enhanced search functionality
    search_query = request.GET.get('search')
    if search_query:
        from django.db.models import Q
        # Split search query into words for better matching
        search_words = search_query.split()
        query = Q()
        
        for word in search_words:
            query |= (
                Q(name__icontains=word) | 
                Q(description__icontains=word)
            )
        
        products = products.filter(query).distinct()
    
    # Price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Availability filter
    in_stock_only = request.GET.get('in_stock')
    if in_stock_only:
        # Get products that have inventory items with quantity > 0
        available_products = models.InventoryItem.objects.filter(quantity__gt=0).values_list('product_id', flat=True)
        products = products.filter(id__in=available_products)
    
    # Add product ratings and review counts
    from django.db.models import Avg, Count
    products = products.annotate(
        average_rating=Avg('productreview__rating'),
        review_count=Count('productreview', distinct=True)
    )
    
    # Sort functionality
    sort_by = request.GET.get('sort')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'newest':
        products = products.order_by('-id')
    elif sort_by == 'popular':
        # Sort by number of orders (most popular first)
        products = products.annotate(
            order_count=Count('orderitem')
        ).order_by('-order_count')
    elif sort_by == 'rating':
        # Sort by highest rating first
        products = products.order_by('-average_rating')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get price range for filters
    from django.db.models import Min, Max
    price_range = models.Product.objects.aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    context = {
        'products': page_obj,
        'search_query': search_query,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'in_stock_only': in_stock_only,
        'price_range': price_range,
        'total_products': paginator.count,
        'product_count_in_cart': product_count_in_cart,
    }
    
    return render(request, 'ecom/index.html', context)

@admin_required
def manage_inventory(request):
    inventory_items = InventoryItem.objects.all()
    if request.method == "POST":
        form = InventoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage-inventory')
    else:
        form = InventoryForm()

    return render(request, 'ecom/manage_inventory.html', {'form': form, 'inventory_items': inventory_items})

def update_stock(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    if request.method == "POST":
        form = InventoryForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('manage-inventory')
    else:
        form = InventoryForm(instance=item)

    return render(request, 'ecom/update_stock.html', {'form': form, 'item': item})




@admin_required
def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return HttpResponseRedirect('adminlogin')


from ecom import utils

def customer_signup_view(request):
    userForm = forms.CustomerUserForm()
    customerForm = forms.CustomerSignupForm()
    mydict = {'userForm': userForm, 'customerForm': customerForm}
    if request.method == 'POST':
        userForm = forms.CustomerUserForm(request.POST)
        customerForm = forms.CustomerSignupForm(request.POST, request.FILES)
        if userForm.is_valid() and customerForm.is_valid():
            user = userForm.save(commit=False)
            user.set_password(userForm.cleaned_data['password'])
            user.save()
            customer = customerForm.save(commit=False)
            customer.user = user

            # Keep raw codes (region code and PSGC codes) so choices and lookups work
            # Names are resolved on display via utils and model properties

            customer.save()
            my_customer_group = Group.objects.get_or_create(name='CUSTOMER')
            my_customer_group[0].user_set.add(user)
            login(request, user)  # Log the user in after registration
            # Clear cart cookies after registration
            response = redirect('customer-home')
            response.delete_cookie('product_ids')
            # Remove all product_*_details cookies
            for key in request.COOKIES.keys():
                if key.startswith('product_') and key.endswith('_details'):
                    response.delete_cookie(key)
            return response
        else:
            # Show errors in the template
            mydict = {'userForm': userForm, 'customerForm': customerForm}
    return render(request, 'ecom/customersignup.html', context=mydict)

def customer_login(request):
  if request.method == 'POST':
    form = CustomerLoginForm(request.POST)
    if form.is_valid():
      username = form.cleaned_data['username']
      password = form.cleaned_data['password']
      user = authenticate(request, username=username, password=password)
      if user is not None:
        login(request, user)
        # Clear cart cookies after login
        response = redirect('home')
        response.delete_cookie('product_ids')
        for key in request.COOKIES.keys():
            if key.startswith('product_') and key.endswith('_details'):
                response.delete_cookie(key)
        return response
      else:
        # Show bottom error via messages when username doesn't exist or password is wrong
        if not User.objects.filter(username=username).exists():
          messages.error(request, 'Account not found. Please try again')
        else:
          messages.error(request, 'Incorrect password')
  else:
    form = CustomerLoginForm()
  return render(request, 'ecom/customerlogin.html', {'form': form})

#-----------for checking user iscustomer
def is_customer(user):
    return user.groups.filter(name='CUSTOMER').exists()

#-----------for checking user is admin
def is_admin(user):
    """
    Check if user is an admin (staff member)
    """
    return user.is_authenticated and user.is_staff

#-----------admin required decorator with security
from functools import wraps
from django.contrib.auth import logout
from django.contrib import messages

def admin_required(view_func):
    """
    Decorator that ensures only admin users can access the view.
    Non-admin users are logged out and redirected to admin login with error message.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated and is admin
        if not request.user.is_authenticated:
            messages.error(request, 'Access denied. Please log in as an administrator.')
            return redirect('adminlogin')
        
        if not is_admin(request.user):
            # Log out the non-admin user for security
            logout(request)
            messages.error(request, 'Access denied. You do not have administrator privileges. You have been logged out for security reasons.')
            return redirect('adminlogin')
        
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@user_passes_test(is_customer)
def add_custom_jersey_to_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get the customer
            customer = models.Customer.objects.get(user=request.user)
            
            # Create a new product for the custom jersey
            custom_jersey = models.Product()
            custom_jersey.name = f'Custom Jersey - {customer.user.username}'
            custom_jersey.price = 99.99  # Set your custom jersey price
            custom_jersey.description = f'Custom jersey with name: {data["playerName"]} and number: {data["playerNumber"]}'
            
            # Convert base64 image to file
            if 'designImage' in data:
                format, imgstr = data['designImage'].split(';base64,')
                ext = format.split('/')[-1]
                image_data = ContentFile(base64.b64decode(imgstr), name=f'custom_jersey_{customer.user.username}.{ext}')
                custom_jersey.product_image = image_data
            
            custom_jersey.save()
            
            # Create order for the custom jersey
            order = models.Orders(
                customer=customer,
                product=custom_jersey,
                status='Pending',
                quantity=1
            )
            order.save()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Invalid request method'})



#---------AFTER ENTERING CREDENTIALS WE CHECK WHETHER USERNAME AND PASSWORD IS OF ADMIN,CUSTOMER
def afterlogin_view(request):
    if is_customer(request.user):
        return redirect('customer-home')
    else:
        return redirect('admin-dashboard')

#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@admin_required
def admin_dashboard_view(request):
    # for cards on dashboard
    customercount = models.Customer.objects.all().count()
    productcount = models.Product.objects.all().count()
    pending_ordercount = models.Orders.objects.filter(status='Pending').count()

    # Prepare users data for Users section
    customers = models.Customer.objects.select_related('user').all()
    users = []
    for c in customers:
        users.append({
            'id': c.id,  # changed from c.get_id
            'name': c.get_name if hasattr(c, 'get_name') else str(c),
            'address': c.get_full_address,
            'phone': c.mobile,
            'status': c.status,
        })

    # Calculate sales analytics
    from django.utils import timezone
    from datetime import timedelta
    current_date = timezone.now()
    last_quarter_start = current_date - timedelta(days=90)
    last_month_start = current_date - timedelta(days=30)

    delivered_orders = models.Orders.objects.filter(status='Delivered').order_by('-created_at')[:10]
    recent_orders = models.Orders.objects.all().order_by('-created_at')[:10]

    # Calculate total sales and period-specific sales
    all_delivered_orders = models.Orders.objects.filter(status='Delivered')
    total_sales = 0
    last_quarter_sales = 0
    last_month_sales = 0

    # Create a dictionary to track product sales
    product_sales = {}

    for order in all_delivered_orders:
        order_items = models.OrderItem.objects.filter(order=order)
        if not order_items.exists():
            continue  # Skip orders with no items
        
        order_total = 0
        for item in order_items:
            item_total = item.price * item.quantity
            order_total += item_total
            
            # Track product-wise sales
            if item.product.id not in product_sales:
                product_sales[item.product.id] = {
                    'name': item.product.name,
                    'quantity_sold': 0,
                    'total_revenue': 0
                }
            product_sales[item.product.id]['quantity_sold'] += item.quantity
            product_sales[item.product.id]['total_revenue'] += item_total
        
        total_sales += order_total
        
        # Calculate period-specific sales
        order_date = order.created_at
        if order_date >= last_quarter_start:
            last_quarter_sales += order_total
            if order_date >= last_month_start:
                last_month_sales += order_total

    for order in delivered_orders:
        order_items = models.OrderItem.objects.filter(order=order)
        if not order_items.exists():
            continue  # Skip orders with no items
        
        order_total = sum(item.price * item.quantity for item in order_items)
        order.total_price = order_total  # Add total_price attribute
        order.order_items = order_items  # Add order_items for template access

    # Sort products by sales performance
    sorted_products = sorted(product_sales.values(), key=lambda x: x['quantity_sold'], reverse=True)
    fast_moving_products = sorted_products[:5] if sorted_products else []
    slow_moving_products = sorted_products[-5:] if len(sorted_products) >= 5 else []

    # Format sales numbers with commas
    formatted_total_sales = '{:,.2f}'.format(total_sales)
    formatted_last_quarter_sales = '{:,.2f}'.format(last_quarter_sales)
    formatted_last_month_sales = '{:,.2f}'.format(last_month_sales)

    # Calculate monthly sales for current year
    from django.db.models.functions import ExtractMonth, ExtractYear
    from django.db.models import Sum, F

    current_year = current_date.year
    # Get monthly sales by aggregating OrderItem data instead of Orders
    monthly_sales_qs = models.OrderItem.objects.filter(
        order__status='Delivered',
        order__created_at__year=current_year
    ).annotate(
        month=ExtractMonth('order__created_at')
    ).values('month').annotate(
        total=Sum(F('price') * F('quantity'))
    ).order_by('month')

    # Initialize list with 12 zeros for each month
    monthly_sales = [0] * 12
    for entry in monthly_sales_qs:
        month_index = entry['month'] - 1
        monthly_sales[month_index] = float(entry['total']) if entry['total'] else 0

    mydict = {
        'customercount': customercount,
        'productcount': productcount,
        'ordercount': pending_ordercount,
        'total_sales': formatted_total_sales,
        'last_quarter_sales': formatted_last_quarter_sales,
        'last_month_sales': formatted_last_month_sales,
        'fast_moving_products': fast_moving_products,
        'slow_moving_products': slow_moving_products,
        'recent_orders': recent_orders,
        'current_date': current_date.strftime('%Y-%m-%d'),
        'monthly_sales': monthly_sales,
        'users': users,
    }
    return render(request, 'ecom/admin_dashboard.html', context=mydict)


# admin view customer table
@admin_required
def admin_view_users(request):
    import csv
    from django.http import HttpResponse

    customers = models.Customer.objects.select_related('user').all()
    users = []
    for c in customers:
        print(f"DEBUG: Customer ID: {c.id}, User ID: {c.user.id if c.user else 'None'}, Name: {c.user.first_name if c.user else 'N/A'} {c.user.last_name if c.user else ''}")
        users.append({
            'id': c.id,
            'user_id': c.user.id if c.user else None,
            'name': f"{c.user.first_name} {c.user.last_name}" if c.user else '',
            'surname': '',
            'customer_id': c.customer_code,
            'email': c.user.email if c.user else '',
            'contact': c.mobile,
            'address': c.get_full_address,
            'balance': getattr(c, 'balance', 0),
            'status': c.status,
            'is_active': c.status == 'Active',
            'wallet_status': getattr(c, 'wallet_status', 'Active'),
            'created_date': c.created_at.strftime('%Y-%m-%d') if hasattr(c, 'created_at') else '',
        })

    if request.GET.get('export') == 'csv':
        # Create the HttpResponse object with CSV header.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users.csv"'

        writer = csv.writer(response)
        # Write CSV header
        writer.writerow(['Customer ID', 'Name', 'Email', 'Contact', 'Address', 'Balance', 'Status', 'Wallet Status', 'Created Date'])

        # Write user data rows
        for user in users:
            writer.writerow([
                user['customer_id'],
                user['name'],
                user['email'],
                user['contact'],
                user['address'],
                user['balance'],
                user['status'],
                user['wallet_status'],
                user['created_date'],
            ])

        return response

    context = {
        'users': users,
        'active_count': sum(1 for u in users if u['status'] == 'Active'),
        'pending_count': sum(1 for u in users if u['status'] == 'Pending'),
        'suspended_count': sum(1 for u in users if u['status'] == 'Suspended'),
        'total_count': len(users),
    }
    return render(request, 'ecom/admin_view_users.html', context)

@admin_required
def bulk_update_users(request):
    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')
        new_status = request.POST.get('bulk_status')

        if user_ids and new_status:
            customers = models.Customer.objects.filter(id__in=user_ids)
            customers.update(status=new_status)
            messages.success(request, f'Successfully updated {len(user_ids)} users to {new_status}')
        else:
            messages.error(request, 'Please select users and status to update')

    return redirect('view-customer')

# admin delete customer
@admin_required
def delete_customer_view(request,pk):
    customer=models.Customer.objects.get(id=pk)
    user=models.User.objects.get(id=customer.user_id)
    user.delete()
    customer.delete()
    return redirect('view-customer')


@admin_required
def update_customer_view(request,pk):
    customer=models.Customer.objects.get(id=pk)
    user=models.User.objects.get(id=customer.user_id)
    userForm=forms.CustomerUserForm(instance=user)
    customerForm=forms.CustomerForm(request.FILES,instance=customer)
    mydict={'userForm':userForm,'customerForm':customerForm}
    if request.method=='POST':
        userForm=forms.CustomerUserForm(request.POST,instance=user)
        customerForm=forms.CustomerForm(request.POST,instance=customer)
        if userForm.is_valid() and customerForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            customerForm.save()
            return redirect('view-customer')
    return render(request,'ecom/admin_update_customer.html',context=mydict)

# admin view the product
@admin_required
def admin_products_view(request):
    # Get all products and order them by id descending (newest first)
    products = models.Product.objects.all().order_by('-id')
    return render(request, 'ecom/admin_products.html', {'products': products})


# admin add product by clicking on floating button
@admin_required
def admin_add_product_view(request):
    productForm=forms.ProductForm()
    if request.method=='POST':
        productForm=forms.ProductForm(request.POST, request.FILES)
        if productForm.is_valid():
            new_product = productForm.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Return JSON response with new product data
                data = {
                    'id': new_product.id,
                    'name': new_product.name,
                    'description': new_product.description,
                    'price': new_product.price,
                    'quantity': new_product.quantity,
                    'size': new_product.size,
                    'product_image_url': new_product.product_image.url if new_product.product_image else '',
                }
                return JsonResponse({'success': True, 'product': data})
            else:
                # After saving, redirect to admin-products page to show updated list including new image
                return HttpResponseRedirect(f'/admin-products?new=1&new_product_id={new_product.id}')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Return form errors as JSON
                errors = productForm.errors.as_json()
                return JsonResponse({'success': False, 'errors': errors})
            else:
                # If form is invalid, render the form with errors
                return render(request,'ecom/admin_add_products.html',{'productForm':productForm})
    return render(request,'ecom/admin_add_products.html',{'productForm':productForm})


from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse

import logging

logger = logging.getLogger(__name__)

@admin_required
@require_POST
@csrf_protect
def delete_product_view(request, pk):
    try:
        product = models.Product.objects.get(id=pk)
        product.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        else:
            return redirect('admin-products')
    except models.Product.DoesNotExist:
        logger.error(f"Product with id {pk} not found for deletion.")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
        else:
            return redirect('admin-products')
    except Exception as e:
        logger.error(f"Error deleting product with id {pk}: {str(e)}")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Error deleting product: ' + str(e)}, status=500)
        else:
            return redirect('admin-products')


@admin_required
def update_product_view(request, pk):
    product = models.Product.objects.get(id=pk)
    if request.method == 'POST':
        productForm = forms.ProductForm(request.POST, request.FILES, instance=product)
        if productForm.is_valid():
            new_size = productForm.cleaned_data.get('size')
            product_name = productForm.cleaned_data.get('name')
            # Check if size changed
            if new_size != product.size:
                # Check if product with same name and new size exists
                try:
                    existing_product = models.Product.objects.get(name=product_name, size=new_size)
                    # Update existing product
                    existing_product.description = productForm.cleaned_data.get('description')
                    existing_product.price = productForm.cleaned_data.get('price')
                    existing_product.quantity = productForm.cleaned_data.get('quantity')
                    if 'product_image' in request.FILES:
                        existing_product.product_image = request.FILES['product_image']
                    existing_product.save()
                except models.Product.DoesNotExist:
                    # Create new product with new size
                    new_product = productForm.save(commit=False)
                    new_product.id = None  # Ensure new object
                    new_product.save()
            else:
                # Size same, update current product
                productForm.save()
            return redirect('admin-products')
    else:
        productForm = forms.ProductForm(instance=product)
    return render(request, 'ecom/admin_update_product.html', {'productForm': productForm})


@admin_required
def admin_view_booking_view(request):
    return redirect('admin-view-processing-orders')

def get_order_status_counts():
    counts = {
        'processing': models.Orders.objects.filter(status__in=['Pending', 'Processing']).count(),
        'confirmed': models.Orders.objects.filter(status='Order Confirmed').count(),
        'shipping': models.Orders.objects.filter(status='Out for Delivery').count(),
        'delivered': models.Orders.objects.filter(status='Delivered').count(),
        'cancelled': models.Orders.objects.filter(status='Cancelled').count(),
    }
    return counts

@admin_required
def admin_view_processing_orders(request):
    orders = models.Orders.objects.filter(status__in=['Pending', 'Processing'])
    counts = get_order_status_counts()
    context = {
        'processing_count': counts.get('processing', 0),
        'confirmed_count': counts.get('confirmed', 0),
        'shipping_count': counts.get('shipping', 0),
        'delivered_count': counts.get('delivered', 0),
        'cancelled_count': counts.get('cancelled', 0),
    }
    return prepare_admin_order_view(request, orders, 'Processing', 'ecom/admin_view_orders.html', extra_context=context)

@admin_required
def admin_view_confirmed_orders(request):
    orders = models.Orders.objects.filter(status='Order Confirmed')
    counts = get_order_status_counts()
    context = {
        'processing_count': counts.get('processing', 0),
        'confirmed_count': counts.get('confirmed', 0),
        'shipping_count': counts.get('shipping', 0),
        'delivered_count': counts.get('delivered', 0),
        'cancelled_count': counts.get('cancelled', 0),
    }
    return prepare_admin_order_view(request, orders, 'Order Confirmed', 'ecom/admin_view_orders.html', extra_context=context)

@admin_required
def admin_view_shipping_orders(request):
    orders = models.Orders.objects.filter(status='Out for Delivery')
    counts = get_order_status_counts()
    context = {
        'processing_count': counts.get('processing', 0),
        'confirmed_count': counts.get('confirmed', 0),
        'shipping_count': counts.get('shipping', 0),
        'delivered_count': counts.get('delivered', 0),
        'cancelled_count': counts.get('cancelled', 0),
    }
    return prepare_admin_order_view(request, orders, 'Out for Delivery', 'ecom/admin_view_orders.html', extra_context=context)

@admin_required
def admin_view_delivered_orders(request):
    orders = models.Orders.objects.filter(status='Delivered')
    counts = get_order_status_counts()
    context = {
        'processing_count': counts.get('processing', 0),
        'confirmed_count': counts.get('confirmed', 0),
        'shipping_count': counts.get('shipping', 0),
        'delivered_count': counts.get('delivered', 0),
        'cancelled_count': counts.get('cancelled', 0),
    }
    return prepare_admin_order_view(request, orders, 'Delivered', 'ecom/admin_view_orders.html', extra_context=context)

@admin_required
def admin_view_cancelled_orders(request):
    orders = models.Orders.objects.filter(status='Cancelled').prefetch_related('orderitem_set').order_by('-created_at')
    counts = get_order_status_counts()
    context = {
        'cancelled_count': counts.get('cancelled', 0),
        'processing_count': counts.get('processing', 0),
        'confirmed_count': counts.get('confirmed', 0),
        'shipping_count': counts.get('shipping', 0),
        'delivered_count': counts.get('delivered', 0),
    }
    return prepare_admin_order_view(request, orders, 'Cancelled', 'ecom/admin_view_orders.html', extra_context=context)


def prepare_admin_order_view(request, orders, status, template, extra_context=None):
    # Order the orders by created_at descending to show new orders first
    orders = orders.order_by('-created_at')
    
    # Prepare a list of orders with their customer, shipping address, and order items
    orders_data = []
    
    for order in orders:
        total_price = 0
        order_items = models.OrderItem.objects.filter(order=order)
        items = []
        for item in order_items:
            items.append({
                'product': item.product,
                'quantity': item.quantity,
                'size': item.size,
                'price': item.price,
                'product_image': item.product.product_image.url if item.product.product_image else None,
            })
            total_price += item.price * item.quantity
        
        # Use order.address if available, else fallback to customer's full address
        shipping_address = order.address if order.address else (order.customer.get_full_address if order.customer else '')
        orders_data.append({
            'order': order,
            'customer': order.customer,
            'shipping_address': shipping_address,
            'order_items': items,
            'status': order.status,
            'order_id': order.order_ref,
            'order_date': order.order_date,
            'total_price': total_price,
        })
    
    context = {
        'orders_data': orders_data,
        'status': status
    }
    if extra_context:
        context.update(extra_context)
    
    return render(request, template, context)

@admin_required
def admin_view_cancelled_orders(request):
    orders = models.Orders.objects.filter(status='Cancelled').prefetch_related('orderitem_set').order_by('-created_at')
    # Prepare orders_data with order_id fallback and total price calculation
    orders_data = []
    for order in orders:
        order_id = order.order_ref if order.order_ref else f"ORD-{order.id}"
        order_items_qs = order.orderitem_set.all()
        order_items = []
        total_price = 0
        for item in order_items_qs:
            price = item.price if item.price else 0
            quantity = item.quantity if item.quantity else 0
            total_price += price * quantity
            order_items.append({
                'product': item.product,
                'quantity': quantity,
                'size': item.size,
                'price': price,
                'product_image': item.product.product_image.url if item.product and item.product.product_image else None,
            })
        orders_data.append({
            'order': order,
            'customer': order.customer,
            'order_items': order_items,
            'order_id': order_id,
            'order_date': order.order_date.strftime('%B %d, %Y') if order.order_date else order.created_at.strftime('%B %d, %Y'),
            'total_price': total_price,
        })
    # Pass orders_data to template
    context = {
        'orders_data': orders_data,
        'status': 'Cancelled',
        'cancelled_count': orders.count(),
    }
    return render(request, 'ecom/admin_view_orders.html', context)


@admin_required
def delete_order_view(request,pk):
    order=models.Orders.objects.get(id=pk)
    order.delete()
    return redirect('admin-view-booking')

# for changing status of order (pending,delivered...)
@admin_required
def update_order_view(request,pk):
    order = models.Orders.objects.get(id=pk)
    orderForm = forms.OrderForm(instance=order)
    
    if request.method == 'POST':
        orderForm = forms.OrderForm(request.POST, instance=order)
        if orderForm.is_valid():
            # Save the form but don't commit yet
            updated_order = orderForm.save(commit=False)
            
            # If status has changed, update the status_updated_at timestamp
            if updated_order.status != order.status:
                updated_order.status_updated_at = timezone.now()
                
                # Set estimated delivery date based on status if not manually set
                if not updated_order.estimated_delivery_date:
                    if updated_order.status == 'Processing':
                        updated_order.estimated_delivery_date = timezone.now().date() + timezone.timedelta(days=7)
                    elif updated_order.status == 'Order Confirmed':
                        updated_order.estimated_delivery_date = timezone.now().date() + timezone.timedelta(days=5)
                    elif updated_order.status == 'Out for Delivery':
                        updated_order.estimated_delivery_date = timezone.now().date() + timezone.timedelta(days=1)
                
                # Reduce inventory when order is marked as delivered
                if updated_order.status == 'Delivered':
                    order_items = updated_order.orderitem_set.all()
                    for order_item in order_items:
                        try:
                            inventory_item = models.InventoryItem.objects.get(product=order_item.product)
                            if inventory_item.quantity >= order_item.quantity:
                                inventory_item.quantity -= order_item.quantity
                                inventory_item.save()
                                messages.success(request, f'Inventory updated: {inventory_item.product.name} quantity reduced by {order_item.quantity}')
                            else:
                                messages.error(request, f'Insufficient inventory for {inventory_item.product.name}')
                                return render(request, 'ecom/update_order.html', {'orderForm': orderForm, 'order': order})
                        except models.InventoryItem.DoesNotExist:
                            messages.warning(request, f'No inventory item found for {order_item.product.name}')
            
            updated_order.save()
            messages.success(request, f'Order status updated to {updated_order.get_status_display()}')
            return redirect('admin-view-booking')
    
    context = {
        'orderForm': orderForm,
        'order': order,
        'status_history': f"Last status update: {order.status_updated_at.strftime('%Y-%m-%d %H:%M:%S') if order.status_updated_at else 'Not available'}"
    }
    return render(request, 'ecom/update_order.html', context)


@admin_required
def delete_inventory(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    item.delete()
    return redirect('manage-inventory')

@admin_required
def bulk_update_orders(request):
    if request.method == 'POST':
        order_ids = request.POST.getlist('order_ids')
        new_status = request.POST.get('bulk_status')
        
        if order_ids and new_status:
            orders = models.Orders.objects.filter(id__in=order_ids)
            current_time = timezone.now()
            
            # Calculate estimated delivery date based on new status
            delivery_date = None
            if new_status == 'Processing':
                delivery_date = current_time.date() + timezone.timedelta(days=7)
            elif new_status == 'Order Confirmed':
                delivery_date = current_time.date() + timezone.timedelta(days=5)
            elif new_status == 'Out for Delivery':
                delivery_date = current_time.date() + timezone.timedelta(days=1)
            
            # If marking as delivered, check and update inventory first
            if new_status == 'Delivered':
                inventory_updates = {}
                
                # First pass: Calculate total quantities needed for each product
                for order in orders:
                    order_items = order.orderitem_set.all()
                    for order_item in order_items:
                        product = order_item.product
                        if product is None:
                            continue
                        if product.id in inventory_updates:
                            inventory_updates[product.id]['quantity_needed'] += order_item.quantity
                        else:
                            inventory_updates[product.id] = {
                                'quantity_needed': order_item.quantity,
                                'orders': [],
                                'product': product
                            }
                        inventory_updates[product.id]['orders'].append(order)
                
                # Second pass: Check inventory availability
                for product_id, update_info in inventory_updates.items():
                    try:
                        inventory_item = models.InventoryItem.objects.get(product=update_info['product'])
                        if inventory_item.quantity >= update_info['quantity_needed']:
                            inventory_item.quantity -= update_info['quantity_needed']
                            inventory_item.save()
                            messages.success(request, f'Inventory updated: {update_info["product"].name} quantity reduced by {update_info["quantity_needed"]}')
                        else:
                            messages.error(request, f'Insufficient inventory for {update_info["product"].name}')
                            return redirect('admin-view-booking')
                    except models.InventoryItem.DoesNotExist:
                        messages.warning(request, f'No inventory item found for {update_info["product"].name}')
            
            # Update all selected orders
            orders.update(
                status=new_status,
                status_updated_at=current_time,
                estimated_delivery_date=delivery_date
            )
            
            messages.success(request, f'Successfully updated {len(order_ids)} orders to {new_status}')
        else:
            messages.error(request, 'Please select orders and status to update')
            
    return redirect('admin-view-booking')

@admin_required
def edit_inventory(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    
    if request.method == "POST":
        form = InventoryForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('manage-inventory')  # Redirect after saving
    else:
        form = InventoryForm(instance=item)

    return render(request, 'ecom/edit_inventory.html', {'form': form, 'item': item})


# admin view the feedback
@admin_required
def view_feedback_view(request):
    feedbacks=models.Feedback.objects.all().order_by('-id')
    return render(request,'ecom/view_feedback.html',{'feedbacks':feedbacks})



#---------------------------------------------------------------------------------
#------------------------ PUBLIC CUSTOMER RELATED VIEWS START ---------------------
#---------------------------------------------------------------------------------
@login_required(login_url='customerlogin')
def pending_orders_view(request):
    try:
        vat_rate = 12
        customer = models.Customer.objects.get(user=request.user)
    except models.Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('customer-home')

    orders = models.Orders.objects.filter(customer=customer, status='Pending').order_by('-order_date', '-created_at')
    orders_with_items = []

    for order in orders:
        order_items = models.OrderItem.objects.filter(order=order)
        products = []
        total = Decimal('0.00')
        for item in order_items:
            # Use VAT-inclusive calculation (same as cart)
            line_total = Decimal(item.price) * item.quantity
            total += line_total
            products.append({
                'item': item,
                'size': item.size,
                'quantity': item.quantity,
                'line_total': line_total,
            })

        # Calculate VAT using same method as cart (VAT-inclusive)
        vat_amount = total * Decimal(12) / Decimal(112)
        net_subtotal = total - vat_amount
        # Use stored delivery fee from order
        delivery_fee = order.delivery_fee
        grand_total = total + Decimal(delivery_fee)

        orders_with_items.append({
            'order': order,
            'products': products,
            'total': total,
            'net_subtotal': net_subtotal,
            'vat_amount': vat_amount,
            'delivery_fee': delivery_fee,
            'grand_total': grand_total,
        })

    return render(request, 'ecom/order_status_page.html', {
        'orders_with_items': orders_with_items,
        'status': 'Pending',
        'title': 'Pending Orders'
    })

@login_required(login_url='customerlogin')
def to_ship_orders_view(request):
    try:
        customer = models.Customer.objects.get(user_id=request.user.id)
    except models.Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('customer-home')
    
    orders = models.Orders.objects.filter(
        customer=customer,
        status__in=['Processing', 'Order Confirmed']
    ).order_by('-order_date')
    orders_with_items = []
    for order in orders:
        order_items = models.OrderItem.objects.filter(order=order)
        products = []
        total = Decimal('0.00')
        for item in order_items:
            # Use VAT-inclusive calculation (same as cart)
            line_total = Decimal(item.price) * item.quantity
            total += line_total
            products.append({
                'item': item,
                'size': item.size,
                'quantity': item.quantity,
                'line_total': line_total,
            })
        
        # Calculate VAT using same method as cart (VAT-inclusive)
        vat_amount = total * Decimal(12) / Decimal(112)
        net_subtotal = total - vat_amount
        # Use stored delivery fee from order
        delivery_fee = order.delivery_fee
        grand_total = total + Decimal(delivery_fee)
        
        orders_with_items.append({
            'order': order,
            'products': products,
            'total': total,
            'net_subtotal': net_subtotal,
            'vat_amount': vat_amount,
            'delivery_fee': delivery_fee,
            'grand_total': grand_total,
        })
    return render(request, 'ecom/order_status_page.html', {'orders_with_items': orders_with_items, 'status': 'To Ship', 'title': 'Orders To Ship'})

@login_required(login_url='customerlogin')
def to_receive_orders_view(request):
    try:
        customer = models.Customer.objects.get(user_id=request.user.id)
    except models.Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('customer-home')
    
    orders = models.Orders.objects.filter(customer=customer, status='Out for Delivery').order_by('-order_date')
    orders_with_items = []
    for order in orders:
        order_items = models.OrderItem.objects.filter(order=order)
        products = []
        total = Decimal('0.00')
        for item in order_items:
            # Use VAT-inclusive calculation (same as cart)
            line_total = Decimal(item.price) * item.quantity
            total += line_total
            products.append({
                'item': item,
                'size': item.size,
                'quantity': item.quantity,
                'line_total': line_total,
            })
        
        # Calculate VAT using same method as cart (VAT-inclusive)
        vat_amount = total * Decimal(12) / Decimal(112)
        net_subtotal = total - vat_amount
        # Use stored delivery fee from order
        delivery_fee = order.delivery_fee
        grand_total = total + Decimal(delivery_fee)
        
        orders_with_items.append({
            'order': order,
            'products': products,
            'total': total,
            'net_subtotal': net_subtotal,
            'vat_amount': vat_amount,
            'delivery_fee': delivery_fee,
            'grand_total': grand_total,
        })
    return render(request, 'ecom/order_status_page.html', {'orders_with_items': orders_with_items, 'status': 'To Receive', 'title': 'Orders To Receive'})

@login_required(login_url='customerlogin')
def delivered_orders_view(request):
    try:
        customer = models.Customer.objects.get(user_id=request.user.id)
    except models.Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('customer-home')
    
    orders = models.Orders.objects.filter(customer=customer, status='Delivered').order_by('-order_date')
    orders_with_items = []
    for order in orders:
        order_items = models.OrderItem.objects.filter(order=order)
        products = []
        total = Decimal('0.00')
        for item in order_items:
            # Use VAT-inclusive calculation (same as cart)
            line_total = Decimal(item.price) * item.quantity
            total += line_total
            products.append({
                'item': item,
                'size': item.size,
                'quantity': item.quantity,
                'line_total': line_total,
            })
        
        # Calculate VAT using same method as cart (VAT-inclusive)
        vat_amount = total * Decimal(12) / Decimal(112)
        net_subtotal = total - vat_amount
        # Use stored delivery fee from order
        delivery_fee = order.delivery_fee
        grand_total = total + Decimal(delivery_fee)
        
        orders_with_items.append({
            'order': order,
            'products': products,
            'total': total,
            'net_subtotal': net_subtotal,
            'vat_amount': vat_amount,
            'delivery_fee': delivery_fee,
            'grand_total': grand_total,
        })
    return render(request, 'ecom/order_status_page.html', {'orders_with_items': orders_with_items, 'status': 'Delivered', 'title': 'Delivered Orders'})

@login_required(login_url='customerlogin')
def cancelled_orders_view(request):
    try:
        customer = models.Customer.objects.get(user_id=request.user.id)
    except models.Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('customer-home')
    
    orders = models.Orders.objects.filter(customer=customer, status='Cancelled').order_by('-status_updated_at')
    orders_with_items = []
    for order in orders:
        order_items = models.OrderItem.objects.filter(order=order)
        products = []
        total = Decimal('0.00')
        for item in order_items:
            # Use VAT-inclusive calculation (same as cart)
            line_total = Decimal(item.price) * item.quantity
            total += line_total
            products.append({
                'item': item,
                'size': item.size,
                'quantity': item.quantity,
                'line_total': line_total,
            })
        
        # Calculate VAT using same method as cart (VAT-inclusive)
        vat_amount = total * Decimal(12) / Decimal(112)
        net_subtotal = total - vat_amount
        # Use stored delivery fee from order
        delivery_fee = order.delivery_fee
        grand_total = total + Decimal(delivery_fee)
        
        orders_with_items.append({
            'order': order,
            'products': products,
            'total': total,
            'net_subtotal': net_subtotal,
            'vat_amount': vat_amount,
            'delivery_fee': delivery_fee,
            'grand_total': grand_total,
        })
    return render(request, 'ecom/order_status_page.html', {'orders_with_items': orders_with_items, 'status': 'Cancelled', 'title': 'Cancelled Orders'})

def cart_page(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)
    
    # Check if cart is empty
    if not cart_items.exists():
        messages.warning(request, 'Your cart is empty!')
        return redirect('customer-home')
        
    paypal_transaction_id = request.GET.get("paypal-payment-id")
    payment_method = request.POST.get("payment_method")
    custid = request.GET.get("custid")

    try:
        customer = Customer.objects.get(id=custid)
    except Customer.DoesNotExist:
        return HttpResponse("Invalid Customer ID")

    cart_items = Cart.objects.filter(user=user)

    # Check if the payment was made with PayPal
    if paypal_transaction_id:
        for cart in cart_items:
            OrderPlaced.objects.create(
                user=user,
                customer=customer,
                product=cart.product,
                quantity=cart.quantity,
                transaction_id=paypal_transaction_id,
            )
            cart.delete()  # Clear the cart after placing the order
        
        return redirect("orders")  # Redirect to order history page
    else:
        return HttpResponse("Invalid payment information")


def search_view(request):
    query = request.GET.get('query')
    if query is not None and query != '':
        products = models.Product.objects.all().filter(name__icontains=query)
    else:
        products = models.Product.objects.all()

    word = "Search Results for: " + query if query else ("Welcome, Guest" if not request.user.is_authenticated else "Welcome, " + request.user.username)

    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter=product_ids.split('|')
        product_count_in_cart=len(set(counter))
    else:
        product_count_in_cart=0

    return render(request,'ecom/customer_home.html',{'products':products,'word':word,'product_count_in_cart':product_count_in_cart, 'search_text': query})


# any one can add product to cart, no need of signin
def add_to_cart_view(request, pk):
    products = models.Product.objects.all()
    
    # Get size and quantity from form if available
    size = request.POST.get('size', 'M')  # Default to M if not provided
    quantity = int(request.POST.get('quantity', 1))  # Default to 1 if not provided
    
    # Check if product with given id and size exists
    try:
        product = models.Product.objects.get(id=pk, size=size)
    except models.Product.DoesNotExist:
        messages.error(request, f'Sorry, size {size} is not available for this product.')
        return redirect('customer-home')
    
    # Check if product quantity is sufficient
    if product.quantity < quantity:
        messages.error(request, f'Sorry, only {product.quantity} pcs available for {product.name} (Size: {size}).')
        return redirect('customer-home')
    
    # For cart counter, fetching products ids added by customer from cookies
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        product_keys = product_ids.split('|')
        product_count_in_cart = len(set(product_keys))
    else:
        product_count_in_cart = 0
    
    # Get next_page from POST or GET with a fallback to home page
    next_page = request.POST.get('next_page') or request.GET.get('next_page', '/')

    # Use consistent cookie key with size
    cookie_key = f'product_{pk}_{size}_details'
    existing_quantity = 0
    if cookie_key in request.COOKIES:
        details = request.COOKIES[cookie_key].split(':')
        if len(details) == 2:
            existing_quantity = int(details[1])

    new_quantity = existing_quantity + quantity

    response = render(request, 'ecom/index.html', {
        'products': products,
        'product_count_in_cart': product_count_in_cart,
        'redirect_to': next_page
    })
    response.set_cookie(cookie_key, f"{size}:{new_quantity}")

    # Update product_ids cookie to include product_{pk}_{size}
    product_key = f'product_{pk}_{size}'
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        product_keys = product_ids.split('|')
        if product_key not in product_keys:
            product_keys.append(product_key)
        updated_product_ids = '|'.join(product_keys)
    else:
        updated_product_ids = product_key
    response.set_cookie('product_ids', updated_product_ids)

    messages.info(request, product.name + f' (Size: {size}) added to cart successfully!')

    return response

def cart_view(request):
    region_choices = Customer.REGION_CHOICES

    # For cart counter
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        product_keys = product_ids.split('|')
        product_count_in_cart = len(set(product_keys))
    else:
        product_count_in_cart = 0

    products = []
    total = 0
    delivery_fee = 0
    region = None
    customer = None
    if request.user.is_authenticated:
        try:
            customer = models.Customer.objects.get(user=request.user)
            region = customer.region
        except models.Customer.DoesNotExist:
            region = None
    # Use dynamic shipping fee lookup
    origin_region = "NCR"
    destination_region = region if region else "NCR"
    delivery_fee = get_shipping_fee(origin_region, destination_region, weight_kg=0.5)
    # ...existing code for products, VAT, etc...
    vat_rate = 12
    vat_multiplier = 1 + (vat_rate / 100)
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        product_keys = product_ids.split('|')
        product_ids_only = set()
        for key in product_keys:
            parts = key.split('_')
            if len(parts) >= 3:
                product_id = parts[1]
                size = '_'.join(parts[2:])
                product_ids_only.add(product_id)
            else:
                product_id = parts[1]
                size = 'M'
                product_ids_only.add(product_id)
        db_products = models.Product.objects.filter(id__in=product_ids_only)
        for p in db_products:
            for key in product_keys:
                if key.startswith(f'product_{p.id}_'):
                    size = key[len(f'product_{p.id}_'):]

                    cookie_key = f'{key}_details'
                    if cookie_key in request.COOKIES:
                        details = request.COOKIES[cookie_key].split(':')
                        if len(details) == 2:
                            size = details[0]
                            quantity = int(details[1])
                            total += p.price * quantity
                            products.append({
                                'product': p,
                                'size': size,
                                'quantity': quantity
                            })
    # Use VAT-inclusive calculation like orders
    vat_amount = total * 12 / 112
    net_subtotal = total - vat_amount
    grand_total = total + delivery_fee
    
    # Get saved addresses for the current user
    saved_addresses = []
    if request.user.is_authenticated and customer:
        saved_addresses = SavedAddress.objects.filter(customer=customer).order_by('-is_default', '-updated_at')
    
    response = render(request, 'ecom/cart.html', {
        'products': products,
        'total': total,
        'delivery_fee': delivery_fee,
        'vat_rate': vat_rate,
        'vat_amount': vat_amount,
        'net_subtotal': net_subtotal,
        'grand_total': grand_total,
        'product_count_in_cart': product_count_in_cart,
        'user_address': customer,
        'region_choices': region_choices,
        'saved_addresses': saved_addresses,
    })
    return response


def remove_from_cart_view(request, pk):
    size = request.GET.get('size', 'M')  # Get size from request, default to M
    
    # For counter in cart
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        product_keys = product_ids.split('|')
        product_count_in_cart = len(set(product_keys))
    else:
        product_count_in_cart = 0

    # Remove only the specific product with the matching size
    specific_key = f'product_{pk}_{size}'
    product_keys_remaining = [key for key in product_keys if key != specific_key]

    products = []
    total = 0

    # Fetch remaining products
    product_ids_only = set()
    for key in product_keys_remaining:
        parts = key.split('_')
        if len(parts) >= 3:
            product_id = parts[1]
            product_ids_only.add(product_id)
        elif len(parts) == 2:
            product_id = parts[1]
            product_ids_only.add(product_id)

    db_products = models.Product.objects.filter(id__in=product_ids_only)

    for p in db_products:
        for key in product_keys_remaining:
            if key.startswith(f'product_{p.id}_'):
                size = key[len(f'product_{p.id}_'):]
                cookie_key = f'{key}_details'
                if cookie_key in request.COOKIES:
                    details = request.COOKIES[cookie_key].split(':')
                    if len(details) == 2:
                        size = details[0]
                        quantity = int(details[1])
                        total += p.price * quantity
                        products.append({
                            'product': p,
                            'size': size,
                            'quantity': quantity
                        })

    # Get next_page from GET with a fallback
    next_page = request.GET.get('next_page', '/')

    # Get customer and region choices
    region_choices = models.Customer.REGION_CHOICES
    customer = None
    region = None
    if request.user.is_authenticated:
        try:
            customer = models.Customer.objects.get(user=request.user)
            region = customer.region
        except models.Customer.DoesNotExist:
            customer = None
            region = None

    # Use dynamic shipping fee lookup (same as orders)
    origin_region = "NCR"
    destination_region = region if region else "NCR"
    delivery_fee = get_shipping_fee(origin_region, destination_region, weight_kg=0.5)

    # Calculate VAT using same method as orders (VAT-inclusive)
    vat_rate = 12
    vat_amount = total * Decimal(vat_rate) / Decimal(112)
    net_subtotal = total - vat_amount
    grand_total = total + Decimal(delivery_fee)

    response = render(request, 'ecom/cart.html', {
        'products': products,
        'total': total,
        'net_subtotal': net_subtotal,
        'delivery_fee': delivery_fee,
        'vat_rate': vat_rate,
        'vat_amount': vat_amount,
        'grand_total': grand_total,
        'product_count_in_cart': product_count_in_cart,
        'user_address': customer,  # Make sure this is passed!
        'region_choices': region_choices,
    })

    # Remove cookie for the specific product-size combination
    cookie_key = f'{specific_key}_details'
    response.delete_cookie(cookie_key)

    # Update product_ids cookie
    if product_keys_remaining:
        response.set_cookie('product_ids', '|'.join(product_keys_remaining))
    else:
        response.delete_cookie('product_ids')

    return response



def send_feedback_view(request):
    feedbackForm=forms.FeedbackForm()
    if request.method == 'POST':
        feedbackForm = forms.FeedbackForm(request.POST)
        if feedbackForm.is_valid():
            feedbackForm.save()
            return render(request, 'ecom/feedback_sent.html')
    return render(request, 'ecom/send_feedback.html', {'feedbackForm':feedbackForm})


#---------------------------------------------------------------------------------
#------------------------ CUSTOMER RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
@never_cache
def customer_home_view(request):
    products = models.Product.objects.all()
    
    # Cart count logic
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0
    
    # Enhanced search functionality
    search_query = request.GET.get('search')
    if search_query:
        from django.db.models import Q
        # Split search query into words for better matching
        search_words = search_query.split()
        query = Q()
        
        for word in search_words:
            query |= (
                Q(name__icontains=word) | 
                Q(description__icontains=word)
            )
        
        products = products.filter(query).distinct()
    
    # Price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Availability filter
    in_stock_only = request.GET.get('in_stock')
    if in_stock_only:
        # Get products that have inventory items with quantity > 0
        available_products = models.InventoryItem.objects.filter(quantity__gt=0).values_list('product_id', flat=True)
        products = products.filter(id__in=available_products)
    
    # Sort functionality
    sort_by = request.GET.get('sort')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'newest':
        products = products.order_by('-id')
    elif sort_by == 'popular':
        # Sort by number of orders (most popular first)
        from django.db.models import Count
        products = products.annotate(
            order_count=Count('orderitem')
        ).order_by('-order_count')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get price range for filters
    from django.db.models import Min, Max
    price_range = models.Product.objects.aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    # Get customer's recent orders for recommendations and wishlist items
    recent_orders = []
    wishlist_product_ids = []
    if request.user.is_authenticated:
        try:
            customer = models.Customer.objects.get(user=request.user)
            recent_orders = models.Orders.objects.filter(customer=customer).order_by('-created_at')[:5]
            # Get wishlist product IDs for current customer
            wishlist_product_ids = list(models.Wishlist.objects.filter(customer=customer).values_list('product_id', flat=True))
        except models.Customer.DoesNotExist:
            pass
    
    # Since there's no Category model, we'll create a simple categories list
    categories = ['T-Shirts', 'Jerseys', 'Hoodies', 'Accessories']
    
    # Get current category from request parameters
    category = request.GET.get('category')
    
    context = {
        'products': page_obj,
        'categories': categories,
        'current_category': category,
        'search_query': search_query,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'in_stock_only': in_stock_only,
        'price_range': price_range,
        'total_products': paginator.count,
        'product_count_in_cart': product_count_in_cart,
        'recent_orders': recent_orders,
        'wishlist_product_ids': wishlist_product_ids,
    }
    
    return render(request, 'ecom/customer_home.html', context)



# shipment address before placing order
@login_required(login_url='customerlogin')
def customer_address_view(request):
    # Check if product is present in cart
    product_in_cart = False
    product_count_in_cart = 0
    total = 0

    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        if product_ids != "":
            product_in_cart = True
            counter = product_ids.split('|')
            product_count_in_cart = len(set(counter))
            
            # Calculate total price
            product_id_in_cart = product_ids.split('|')
            products = models.Product.objects.all().filter(id__in=product_id_in_cart)
            for p in products:
                # Calculate quantity from cookies for each product
                quantity = 1
                for key in product_ids.split('|'):
                    if key.startswith(f'product_{p.id}_'):
                        cookie_key = f'{key}_details'
                        if cookie_key in request.COOKIES:
                            details = request.COOKIES[cookie_key].split(':')
                            if len(details) == 2:
                                quantity = int(details[1])
                total += p.price * quantity

    # Get payment method from query parameter
    payment_method = request.GET.get('method', 'cod')

    # For COD, skip address form and use profile address
    if payment_method == 'cod':
        if not product_in_cart:
            return render(request, 'ecom/customer_address.html', {
                'product_in_cart': product_in_cart,
                'product_count_in_cart': product_count_in_cart
            })
        
        # Redirect directly to payment success for COD
        return redirect(f'/payment-success?method=cod')

    # For other payment methods, show address form
    addressForm = forms.AddressForm()
    if request.method == 'POST':
        addressForm = forms.AddressForm(request.POST)
        if addressForm.is_valid():
            email = addressForm.cleaned_data['Email']
            mobile = addressForm.cleaned_data['Mobile']
            address = addressForm.cleaned_data['Address']

            response = render(request, 'ecom/payment.html', {'total': total})
            response.set_cookie('email', email)
            response.set_cookie('mobile', mobile)
            response.set_cookie('address', address)
            return response

    return render(request, 'ecom/customer_address.html', {
        'addressForm': addressForm,
        'product_in_cart': product_in_cart,
        'product_count_in_cart': product_count_in_cart,
        'payment_method': payment_method
    })

@login_required(login_url='customerlogin')
def payment_success_view(request):
    import uuid
    try:
        customer = models.Customer.objects.get(user_id=request.user.id)
    except models.Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('customer-home')
    
    products = []
    payment_method = request.GET.get('method', 'cod')  # Default to COD if not specified

    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        if product_ids != "":
            product_keys = request.COOKIES['product_ids'].split('|')
            product_ids_only = set()
            for key in product_keys:
                parts = key.split('_')
                if len(parts) >= 3:
                    product_id = parts[1]
                    product_ids_only.add(product_id)
            products = list(models.Product.objects.filter(id__in=product_ids_only))

    # For COD, use customer's profile information
    if payment_method == 'cod':
        email = customer.user.email
        mobile = str(customer.mobile)
        address = customer.get_full_address
    else:
        # For other payment methods (e.g., PayPal), use provided address
        email = request.COOKIES.get('email', customer.user.email)
        mobile = request.COOKIES.get('mobile', str(customer.mobile))
        address = request.COOKIES.get('address', customer.get_full_address)

    # Generate a unique short order reference ID
    import random
    import string
    def generate_order_ref(length=12):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    order_ref = generate_order_ref()

    # Calculate delivery fee using same logic as cart
    region = customer.region if hasattr(customer, 'region') else None
    origin_region = "NCR"
    destination_region = region if region else "NCR"
    delivery_fee = get_shipping_fee(origin_region, destination_region, weight_kg=0.5)

    # Create the parent order entry with order_ref and delivery_fee
    initial_status = 'Processing' if payment_method == 'paypal' else 'Pending'
    parent_order = models.Orders.objects.create(
        customer=customer,
        status=initial_status,
        email=email,
        mobile=mobile,
        address=address,
        payment_method=payment_method,
        order_date=timezone.now(),
        status_updated_at=timezone.now(),
        notes=f"Order Group ID: {order_ref}",
        order_ref=order_ref,
        delivery_fee=delivery_fee
    )

    # Create order items linked to the parent order
    for product in (products or []):
        quantity = 1  # Default quantity to 1
        size = 'M'  # Default size
        for key in product_keys:
            if key.startswith(f'product_{product.id}_'):
                cookie_key = f'{key}_details'
                if cookie_key in request.COOKIES:
                    details = request.COOKIES[cookie_key].split(':')
                    if len(details) == 2:
                        size = details[0]
                        quantity = int(details[1])

                # Create order item linked to parent order with size
                models.OrderItem.objects.create(
                    order=parent_order,
                    product=product,
                    quantity=quantity,
                    price=product.price,
                    size=size
                )

                # Decrease product quantity
                product.quantity = max(0, product.quantity - quantity)
                product.save()
                print(f"Product {product.id} quantity decreased by {quantity}. New quantity: {product.quantity}")

                # Update inventory item quantity
                try:
                    inventory_item = models.InventoryItem.objects.get(name=product.name)
                    if inventory_item.quantity >= quantity:
                        inventory_item.quantity = max(0, inventory_item.quantity - quantity)
                        inventory_item.save()
                        print(f"Inventory item {inventory_item.name} quantity decreased by {quantity}. New quantity: {inventory_item.quantity}")
                    else:
                        print(f"Warning: Insufficient inventory for {inventory_item.name}")
                except models.InventoryItem.DoesNotExist:
                    print(f"Warning: No inventory item found for product {product.name}")

    # Clear cookies after order placement
    response = render(request, 'ecom/payment_success.html')
    response.delete_cookie('product_ids')

    # Only clear address cookies for non-COD payments
    if payment_method != 'cod':
        response.delete_cookie('email')
        response.delete_cookie('mobile')
        response.delete_cookie('address')

    # Clear product-specific cookies
    for product in (products or []):
        for key in product_keys:
            if key.startswith(f'product_{product.id}_'):
                cookie_key = f'{key}_details'
                response.delete_cookie(cookie_key)

    return response

def place_order(request):
    print('Place Order view function executed')
    if request.method == 'POST':
        print('POST request received')
        customer = models.Customer.objects.get(user_id=request.user.id)
        
        # Get address from cookies if available, otherwise use customer's profile address
        address = request.COOKIES.get('address', customer.get_full_address)
        mobile = request.COOKIES.get('mobile', customer.mobile)
        
        # Create the order with the appropriate address
        order = Orders.objects.create(
            customer=customer,
            email=request.user.email,
            address=address,
            mobile=mobile,
            status='Pending',
            order_date=timezone.now()
        )
        
        design_data = request.POST.get('design_data')
        if design_data:
            # Handle custom design data if present
            print('Design data:', design_data)
            # Add custom design processing logic here
            
        print('Order created:', order)
        return JsonResponse({'message': 'Order placed successfully'})
    else:
        print('Invalid request method')
        return JsonResponse({'message': 'Invalid request method'}, status=400)

@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def cancel_order_view(request, order_id):
    try:
        customer = models.Customer.objects.get(user_id=request.user.id)
        order = models.Orders.objects.get(id=order_id, customer=customer)
        if order.status == 'Pending':
            # Restore stock for each item in the order
            order_items = models.OrderItem.objects.filter(order=order)
            for item in order_items:
                product = item.product
                product.quantity += item.quantity
                product.save()
            order.status = 'Cancelled'
            order.status_updated_at = timezone.now()
            order.save()
            messages.success(request, 'Order cancelled successfully!')
        else:
            messages.error(request, 'Order cannot be cancelled at this time.')
    except models.Orders.DoesNotExist:
        messages.error(request, 'Order not found.')
    except models.Customer.DoesNotExist:
        messages.error(request, 'Customer not found.')
    return redirect('cancelled-orders')




@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def my_order_view(request):
    try:
        customer = models.Customer.objects.get(user_id=request.user.id)
    except models.Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('customer-home')
    orders = models.Orders.objects.filter(customer=customer).order_by('-order_date')
    orders_with_items = []
    for order in orders:
        order_items = models.OrderItem.objects.filter(order=order)
        total_price = 0
        for item in order_items:
            total_price += item.price * item.quantity
        order.total = total_price
        orders_with_items.append({
            'order': order,
            'items': order_items
        })
    return render(request, 'ecom/my_order.html', {'orders_with_items': orders_with_items})

@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def my_order_view_pk(request, pk):
    customer = models.Customer.objects.get(user_id=request.user.id)
    order = get_object_or_404(models.Orders, id=pk, customer=customer)
    order_items = order.orderitem_set.all()
    return render(request, 'ecom/order_detail.html', {'order': order, 'order_items': order_items})

def my_view(request):
    facebook_url = reverse('facebook')
    
def my_view(request):
    instagram_url = reverse('instagram')


import io
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse
from django.template.loader import render_to_string


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result, encoding='UTF-8')
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None



def download_invoice_view(request, order_id):
    order = models.Orders.objects.get(id=order_id)
    order_items = models.OrderItem.objects.filter(order=order)
    customer = order.customer

    # Use dynamic shipping fee lookup (same as pending_orders_view)
    region = customer.region if hasattr(customer, 'region') else None
    origin_region = "NCR"
    destination_region = region if region else "NCR"
    delivery_fee = Decimal(str(get_shipping_fee(origin_region, destination_region, weight_kg=0.5)))

    subtotal = Decimal('0.00')
    products = []
    for item in order_items:
        line_total = Decimal(item.price) * item.quantity
        subtotal += line_total
        products.append({
            'item': item,
            'size': item.size,
            'quantity': item.quantity,
            'unit_price': Decimal(item.price),
            'line_total': line_total,
        })

    net_subtotal = subtotal / Decimal('1.12')
    vat_amount = subtotal - net_subtotal
    grand_total = subtotal + delivery_fee

    context = {
        'order': order,
        'products': products,
        'net_subtotal': net_subtotal,
        'vat_amount': vat_amount,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'grand_total': grand_total,
        'customer': customer,
    }

    html = render_to_string('ecom/download_invoice.html', context)
    # ...PDF generation logic or return HttpResponse(html)...
    return HttpResponse(html)

def pre_order(request):
    return render(request, 'ecom/pre_order.html')


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def my_profile_view(request):
    try:
        customer=models.Customer.objects.get(user_id=request.user.id)
        return render(request,'ecom/my_profile.html',{'customer':customer})
    except models.Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('customer-home')


@user_passes_test(is_customer)
def edit_profile_view(request):
    try:
        customer = models.Customer.objects.get(user_id=request.user.id)
        user = models.User.objects.get(id=customer.user_id)
    except (models.Customer.DoesNotExist, models.User.DoesNotExist):
        messages.error(request, 'Profile not found. Please contact support.')
        return redirect('customer-home')
    
    if request.method == 'POST':
        userForm = forms.CustomerUserForm(request.POST, instance=user)
        customerForm = forms.CustomerForm(request.POST, request.FILES, instance=customer)
        
        if userForm.is_valid() and customerForm.is_valid():
            # Save user without changing password if it's empty
            if not userForm.cleaned_data['password']:
                del userForm.cleaned_data['password']
                user = userForm.save(commit=False)
            else:
                user = userForm.save(commit=False)
                user.set_password(userForm.cleaned_data['password'])
            user.save()
            
            # Save customer form
            customer = customerForm.save(commit=False)
            customer.user = user
            customer.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('my-profile')
        else:
            # Add specific error messages for each form
            for field, errors in userForm.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            for field, errors in customerForm.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        userForm = forms.CustomerUserForm(instance=user)
        customerForm = forms.CustomerForm(instance=customer)
    
    return render(request, 'ecom/edit_profile.html', {
        'userForm': userForm,
        'customerForm': customerForm
    })




#---------------------------------------------------------------------------------
#------------------------ ABOUT US AND CONTACT US VIEWS START --------------------
#---------------------------------------------------------------------------------
def aboutus_view(request):
    return render(request,'ecom/about.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message, settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently = False)
            return render(request, 'ecom/contactussuccess.html')
    return render(request, 'ecom/contactus.html', {'form':sub})

def jersey_customizer(request):
    return render(request, 'ecom/customizer.html')


@login_required(login_url='customerlogin')
def home(request):
    return render(request, 'ecom/home.html')

def manage_profile(request):
    return render(request, 'ecom/manage_profile.html')

def create(request):
    return render(request, 'ecom/create.html')

def jersey_customizer_advanced_view(request):
    return render(request, 'ecom/jersey_customizer_advanced.html')

def jersey_customizer_3d_view(request):
    return render(request, 'ecom/jersey_customizer_3d.html')

def jersey_customizer(request):
    return render(request, 'ecom/jersey_customizer.html')

def jersey_template(request):
    return render(request, 'ecom/jersey_template.html')

def interactive_jersey(request):
    return render(request, 'ecom/interactive_jersey.html')


#-----------------------------------------------------------
#------------------------ PAYMONGO -------------------------
#-----------------------------------------------------------

# Replace with your own PayMongo test key
PAYMONGO_SECRET_KEY = 'sk_test_FFfnvsMb2YQSctcZ3NY8wThb'

def create_gcash_payment(request):
    url = "https://api.paymongo.com/v1/checkout_sessions"
    headers = {
        "Authorization": f"Basic {PAYMONGO_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    # Extract product details from cookies or session (example using cookies)
    product_ids = request.COOKIES.get('product_ids', '')
    if not product_ids:
        return JsonResponse({"error": "No products in cart"}, status=400)

    product_keys = product_ids.split('|')
    product_details = []
    total_amount = 0

    # Use a list to preserve order of products as in cart
    for key in product_keys:
        cookie_key = f"{key}_details"
        if cookie_key in request.COOKIES:
            details = request.COOKIES[cookie_key].split(':')
            if len(details) == 2:
                size = details[0]
                quantity = int(details[1])
                # Extract product id from key format: product_{id}_{size}
                parts = key.split('_')
                if len(parts) >= 2:
                    product_id = parts[1]
                    try:
                        product = models.Product.objects.get(id=product_id)
                        # Ensure product.price is decimal or float, convert to int cents properly
                        unit_price_cents = int(round(float(product.price) * 100))
                        total_amount += unit_price_cents * quantity
                        print(f"DEBUG: Product: {product.name}, Unit Price: {product.price}, Quantity: {quantity}, Amount (cents): {unit_price_cents * quantity}")
                        product_details.append({
                            "currency": "PHP",
                            "amount": unit_price_cents,
                            "name": f"{product.name} (Size: {size})",
                            "quantity": quantity
                        })
                    except models.Product.DoesNotExist:
                        continue

    if not product_details:
        return JsonResponse({"error": "No valid products found"}, status=400)

    payload = {
        "data": {
            "attributes": {
                "billing": {
                    "name": "Juan Dela Cruz",
                    "email": "juan@example.com",
                    "phone": "+639171234567"
                },
                "send_email_receipt": False,
                "show_line_items": True,
                "line_items": product_details,
                "payment_method_types": ["gcash"],
                "description": f"GCash Payment for {len(product_details)} item(s)",
                "success_url": "http://127.0.0.1:8000/payment-success/",
                "cancel_url": "http://127.0.0.1:8000/payment-cancel/"
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload, auth=(PAYMONGO_SECRET_KEY, ''))
    data = response.json()

    try:
        checkout_url = data['data']['attributes']['checkout_url']
        return redirect(checkout_url)
    except KeyError:
        return JsonResponse({"error": "Payment creation failed", "details": data}, status=400)

from django.views.decorators.http import require_GET
from django.core.serializers.json import DjangoJSONEncoder
import datetime

@require_GET
@admin_required
def get_transactions_by_month(request):
    month = request.GET.get('month')
    year = request.GET.get('year')
    if not month or not year:
        return JsonResponse({'error': 'Month and year parameters are required'}, status=400)
    try:
        month = int(month)
        year = int(year)
    except ValueError:
        return JsonResponse({'error': 'Invalid month or year parameter'}, status=400)

    # Filter delivered orders by month and year, and only those with a customer
    orders = models.Orders.objects.filter(
        status='Delivered',
        order_date__year=year,
        order_date__month=month,
        customer__isnull=False
    ).select_related('customer').order_by('-order_date')[:20]

    transactions = []
    for order in orders:
        transactions.append({
            'user_name': f"{order.customer.user.first_name} {order.customer.user.last_name}" if order.customer and order.customer.user else 'Unknown',
            'order_id': order.order_ref,
            'date': order.order_date.strftime('%Y-%m-%d'),
            'amount': sum(float(item.product.price) * item.quantity for item in order.orderitem_set.all() if item.product and item.product.price),
            'type': 'credit'  # Assuming all delivered orders are credits
        })

    return JsonResponse({'transactions': transactions}, encoder=DjangoJSONEncoder)

def payment_cancel(request):
    return HttpResponse("❌ Payment canceled.")

from ecom import utils

@login_required
def update_address(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        try:
            customer = Customer.objects.get(user=request.user)
        except Customer.DoesNotExist:
            messages.error(request, 'Customer profile not found.')
            return redirect('cart')
        customer.full_name = request.POST.get('full_name')
        # Store raw codes without conversion
        customer.region = request.POST.get('region')
        customer.province = request.POST.get('province')
        customer.citymun = request.POST.get('citymun')
        customer.barangay = request.POST.get('barangay')
        street = request.POST.get('street_address')
        if street is None or street.strip() == '':
            messages.error(request, 'Street address is required.')
            return redirect('cart')
        customer.street_address = street
        customer.postal_code = request.POST.get('postal_code')
        customer.save()

        # Sync address details to all not-yet-shipped orders (e.g., Pending/Processing)
        try:
            new_address = customer.get_full_address
            origin_region = "NCR"
            destination_region = customer.region if getattr(customer, 'region', None) else "NCR"
            new_delivery_fee = Decimal(str(get_shipping_fee(origin_region, destination_region, weight_kg=0.5)))

            Orders.objects.filter(
                customer=customer,
                status__in=['Pending', 'Processing', 'Order Confirmed']
            ).update(
                address=new_address,
                email=request.user.email,
                mobile=str(customer.mobile),
                delivery_fee=new_delivery_fee
            )
        except Exception as e:
            # Don't block the UX if order sync fails; just log and continue
            logger.warning(f"Order address sync failed: {e}")

        messages.success(request, 'Address updated successfully!')
        return redirect('cart')
    return redirect('cart')


@admin_required
def admin_manage_inventory_view(request):
    if request.method == "POST":
        form = InventoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin-manage-inventory')
    else:
        form = InventoryForm()

    inventory_items = models.InventoryItem.objects.all()

    total_items = inventory_items.count()
    from django.db.models import F
    # The field is named 'low_stock_threshold' in the form, but in the model it seems to be 'description' or missing
    # From error, low_stock_threshold is not a field in InventoryItem model
    # So we will treat low_stock_threshold as a constant threshold, e.g., 10
    LOW_STOCK_THRESHOLD = 10
    low_stock_items = inventory_items.filter(quantity__lte=LOW_STOCK_THRESHOLD, quantity__gt=0).count()
    out_of_stock_items = inventory_items.filter(quantity=0).count()
    from django.db.models import Sum
    total_stock = inventory_items.aggregate(total=Sum('quantity'))['total'] or 0

    return render(request, 'ecom/admin_manage_inventory.html', {
        'inventory_items': inventory_items,
        'form': form,
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
        'total_stock': total_stock,
    })

def get_shipping_fee(origin_region, destination_region, weight_kg=0.5):
    from .models import ShippingFee
    
    # Region mapping from customer format to shipping fee format
    region_mapping = {
        'Region R1': 'Region I',
        'Region R2': 'Region II', 
        'Region R3': 'Region III',
        'Region R4A': 'Region IV-A',
        'Region R4B': 'Region IV-B',
        'Region R5': 'Region V',
        'Region R6': 'Region VI',
        'Region R7': 'Region VII',
        'Region R8': 'Region VIII',
        'Region R9': 'Region IX',
        'Region R10': 'Region X',
        'Region R11': 'Region XI',
        'Region R12': 'Region XII',
        'Region R13': 'Region XIII',
        'NCR': 'NCR',
        'CAR': 'CAR',
        'BARMM': 'BARMM'
    }
    
    # Map regions to proper format
    mapped_origin = region_mapping.get(origin_region, origin_region)
    mapped_destination = region_mapping.get(destination_region, destination_region)
    
    try:
        # Find the shipping fee with weight greater than or equal to the requested weight
        fee = ShippingFee.objects.filter(
            courier="Standard",
            origin_region=mapped_origin,
            destination_region=mapped_destination,
            weight_kg__gte=weight_kg
        ).order_by('weight_kg').first()
        
        if fee:
            return float(fee.price_php)
        else:
            # Default fee if no matching record found
            return 50.0
    except Exception as e:
        print(f"Error getting shipping fee: {e}")
        return 50.0

@login_required
def save_new_address(request):
    if request.method == 'POST':
        try:
            customer = Customer.objects.get(user=request.user)
            address = SavedAddress(
                customer=customer,
                region=request.POST.get('region'),
                province=request.POST.get('province'),
                citymun=request.POST.get('citymun'),
                barangay=request.POST.get('barangay'),
                street_address=request.POST.get('street_address'),
                postal_code=request.POST.get('postal_code'),
                is_default=not SavedAddress.objects.filter(customer=customer).exists()  # Make first address default
            )
            address.save()
            
            # Check if request came from cart page via HTTP_REFERER
            referer = request.META.get('HTTP_REFERER', '')
            if 'cart' in referer:
                # Return JSON response for cart page (AJAX handling)
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Address saved successfully!',
                    'redirect': False  # Don't redirect, stay on cart
                })
            else:
                # For manage-addresses page, return success for page reload
                messages.success(request, 'New address saved successfully!')
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Address saved successfully',
                    'redirect': True  # Allow page reload
                })
        except Customer.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Customer profile not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def get_saved_addresses(request):
    try:
        customer = Customer.objects.get(user=request.user)
        addresses = SavedAddress.objects.filter(customer=customer)
        addresses_data = [{
            'id': addr.id,
            'region': addr.get_region_display() if hasattr(addr, 'get_region_display') else addr.region,
            'province': addr.province,
            'citymun': addr.citymun,
            'barangay': addr.barangay,
            'street_address': addr.street_address,
            'postal_code': addr.postal_code,
            'is_default': addr.is_default
        } for addr in addresses]
        return JsonResponse({'status': 'success', 'addresses': addresses_data})
    except Customer.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Customer not found'}, status=404)

@login_required
def set_default_address(request, address_id):
    if request.method == 'POST':
        try:
            customer = Customer.objects.get(user=request.user)
            address = SavedAddress.objects.get(id=address_id, customer=customer)
            
            # Remove default status from all other addresses
            SavedAddress.objects.filter(customer=customer).update(is_default=False)
            
            # Set new default address
            address.is_default = True
            address.save()
            
            # Update customer's current address
            customer.region = address.region
            customer.province = address.province
            customer.citymun = address.citymun
            customer.barangay = address.barangay
            customer.street_address = address.street_address
            customer.postal_code = address.postal_code
            customer.save()

            # Sync updated default address to all not-yet-shipped orders
            try:
                new_address = customer.get_full_address
                origin_region = "NCR"
                destination_region = customer.region if getattr(customer, 'region', None) else "NCR"
                new_delivery_fee = Decimal(str(get_shipping_fee(origin_region, destination_region, weight_kg=0.5)))

                Orders.objects.filter(
                    customer=customer,
                    status__in=['Pending', 'Processing', 'Order Confirmed']
                ).update(
                    address=new_address,
                    email=request.user.email,
                    mobile=str(customer.mobile),
                    delivery_fee=new_delivery_fee
                )
            except Exception as e:
                logger.warning(f"Default address order sync failed: {e}")
            
            return JsonResponse({'status': 'success', 'message': 'Default address updated successfully'})
        except (Customer.DoesNotExist, SavedAddress.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Address not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def delete_address(request, address_id):
    if request.method == 'POST':
        try:
            customer = Customer.objects.get(user=request.user)
            address = SavedAddress.objects.get(id=address_id, customer=customer)
            if not address.is_default:  # Prevent deletion of default address
                address.delete()
                return JsonResponse({'status': 'success', 'message': 'Address deleted successfully'})
            return JsonResponse({'status': 'error', 'message': 'Cannot delete default address'}, status=400)
        except (Customer.DoesNotExist, SavedAddress.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Address not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def manage_addresses_view(request):
    """View for managing customer addresses on a dedicated page"""
    customer = Customer.objects.get(user=request.user)
    saved_addresses = SavedAddress.objects.filter(customer=customer).order_by('-is_default', '-updated_at')
    
    context = {
        'saved_addresses': saved_addresses,
    }
    return render(request, 'ecom/manage_addresses.html', context)

# AI Designer View
def ai_designer_view(request):
    """
    AI-powered 2D designer page for creating custom designs
    """
    return render(request, 'ecom/ai_designer.html')


# Automated Delivery System Views
import secrets
import hashlib
from datetime import timedelta
from django.utils import timezone
from .models import DeliveryMagicLink, DeliveryStatusLog, BulkOrderOperation

@admin_required
def quick_progress_order(request, order_id):
    """Quick one-click order status progression"""
    try:
        order = get_object_or_404(Orders, id=order_id)
        
        # Define status progression mapping
        status_progression = {
            'Pending': 'Processing',
            'Processing': 'Order Confirmed',
            'Order Confirmed': 'Out for Delivery',
            'Out for Delivery': 'Delivered',
        }
        
        current_status = order.status
        next_status = status_progression.get(current_status)
        
        if not next_status:
            return JsonResponse({
                'success': False, 
                'message': f'Cannot progress from {current_status}'
            })
        
        # Log the status change
        DeliveryStatusLog.objects.create(
            order=order,
            previous_status=current_status,
            new_status=next_status,
            updated_by=request.user.username,
            update_method='dashboard',
            notes=f'Quick progression from {current_status} to {next_status}'
        )
        
        # Update order status
        order.status = next_status
        order.status_updated_at = timezone.now()
        order.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Order progressed from {current_status} to {next_status}',
            'new_status': next_status
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating order: {str(e)}'
        })

@admin_required
def bulk_progress_orders(request):
    """Bulk progress multiple orders to next status"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_ids = data.get('order_ids', [])
            
            if not order_ids:
                return JsonResponse({'success': False, 'message': 'No orders selected'})
            
            # Create bulk operation record
            bulk_op = BulkOrderOperation.objects.create(
                operation_type='bulk_progress',
                performed_by=request.user,
                parameters={'order_ids': order_ids}
            )
            
            success_count = 0
            errors = []
            
            status_progression = {
                'Pending': 'Processing',
                'Processing': 'Order Confirmed',
                'Order Confirmed': 'Out for Delivery',
                'Out for Delivery': 'Delivered',
            }
            
            for order_id in order_ids:
                try:
                    order = Orders.objects.get(id=order_id)
                    current_status = order.status
                    next_status = status_progression.get(current_status)
                    
                    if next_status:
                        # Log the status change
                        DeliveryStatusLog.objects.create(
                            order=order,
                            previous_status=current_status,
                            new_status=next_status,
                            updated_by=request.user.username,
                            update_method='bulk_progress',
                            notes=f'Bulk progression from {current_status} to {next_status}'
                        )
                        
                        order.status = next_status
                        order.status_updated_at = timezone.now()
                        order.save()
                        
                        bulk_op.orders_affected.add(order)
                        success_count += 1
                    else:
                        errors.append(f'Order {order.order_ref}: Cannot progress from {current_status}')
                        
                except Orders.DoesNotExist:
                    errors.append(f'Order ID {order_id} not found')
                except Exception as e:
                    errors.append(f'Order ID {order_id}: {str(e)}')
            
            # Update bulk operation
            bulk_op.completed_at = timezone.now()
            bulk_op.success_count = success_count
            bulk_op.error_count = len(errors)
            bulk_op.errors = errors
            bulk_op.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully progressed {success_count} orders',
                'errors': errors
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Bulk operation failed: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@admin_required
def generate_magic_link(request, order_id):
    """Generate a magic link for external delivery status updates"""
    try:
        order = get_object_or_404(Orders, id=order_id)
        
        # Check if magic link already exists
        try:
            magic_link = DeliveryMagicLink.objects.get(order=order)
            if not magic_link.is_expired and magic_link.is_active:
                return JsonResponse({
                    'success': True,
                    'message': 'Magic link already exists',
                    'status_url': request.build_absolute_uri(magic_link.get_status_url()),
                    'token': magic_link.token
                })
        except DeliveryMagicLink.DoesNotExist:
            pass
        
        # Generate new magic link
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(days=30)  # 30 days expiry
        
        magic_link = DeliveryMagicLink.objects.create(
            order=order,
            token=token,
            expires_at=expires_at
        )
        
        status_url = request.build_absolute_uri(magic_link.get_status_url())
        
        return JsonResponse({
            'success': True,
            'message': 'Magic link generated successfully',
            'status_url': status_url,
            'token': token,
            'expires_at': expires_at.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error generating magic link: {str(e)}'
        })

def magic_link_update(request, token, action):
    """Handle external delivery status updates via magic link"""
    try:
        magic_link = get_object_or_404(DeliveryMagicLink, token=token, is_active=True)
        
        if magic_link.is_expired:
            return render(request, 'ecom/magic_link_expired.html', {
                'order': magic_link.order
            })
        
        order = magic_link.order
        
        # Define allowed actions and their corresponding statuses
        action_mapping = {
            'confirm': 'Processing',
            'ship': 'Out for Delivery',
            'deliver': 'Delivered',
            'cancel': 'Cancelled'
        }
        
        if action not in action_mapping:
            return render(request, 'ecom/magic_link_error.html', {
                'error': 'Invalid action',
                'order': order
            })
        
        new_status = action_mapping[action]
        previous_status = order.status
        
        # Update order status
        order.status = new_status
        order.status_updated_at = timezone.now()
        order.save()
        
        # Log the status change
        DeliveryStatusLog.objects.create(
            order=order,
            previous_status=previous_status,
            new_status=new_status,
            updated_by='External (Magic Link)',
            update_method='magic_link',
            notes=f'Status updated via magic link action: {action}'
        )
        
        return render(request, 'ecom/magic_link_success.html', {
            'order': order,
            'action': action,
            'previous_status': previous_status,
            'new_status': new_status
        })
        
    except Exception as e:
        return render(request, 'ecom/magic_link_error.html', {
            'error': str(e)
        })

# New Automated Delivery API Views for Admin Interface
@csrf_protect
def initiate_automated_delivery(request, order_id):
    """Initiate automated delivery process for an order"""
    # Check authentication for AJAX requests
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)
    
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized access'}, status=403)
    
    if request.method == 'POST':
        try:
            order = get_object_or_404(Orders, id=order_id)
            
            if order.status != 'Order Confirmed':
                return JsonResponse({
                    'success': False,
                    'message': 'Order must be in "Order Confirmed" status to initiate delivery'
                })
            
            # Update order status to "Out for Delivery"
            previous_status = order.status
            order.status = 'Out for Delivery'
            order.status_updated_at = timezone.now()
            
            # Set estimated delivery date (1 day from now)
            if not order.estimated_delivery_date:
                order.estimated_delivery_date = timezone.now().date() + timedelta(days=1)
            
            order.save()
            
            # Log the status change
            DeliveryStatusLog.objects.create(
                order=order,
                previous_status=previous_status,
                new_status='Out for Delivery',
                updated_by=request.user.username,
                update_method='automated_delivery',
                notes='Automated delivery process initiated'
            )
            
            # Generate tracking number if not exists
            if not hasattr(order, 'tracking_number') or not order.tracking_number:
                order.tracking_number = f"TRK{order.id:06d}{timezone.now().strftime('%Y%m%d')}"
                order.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Automated delivery initiated successfully',
                'new_status': 'Out for Delivery',
                'tracking_number': getattr(order, 'tracking_number', None)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error initiating delivery: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_protect
def track_delivery_status(request, order_id):
    """Get delivery tracking information for an order"""
    # Check authentication for AJAX requests
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)
    
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized access'}, status=403)
    
    try:
        order = get_object_or_404(Orders, id=order_id)
        
        if order.status not in ['Out for Delivery', 'Delivered']:
            return JsonResponse({
                'success': False,
                'message': 'Order is not in delivery status'
            })
        
        # Get latest status logs
        latest_logs = order.status_logs.all()[:5]
        
        # Simulate tracking information (in real implementation, this would integrate with delivery service API)
        tracking_info = {
            'status': order.status,
            'current_location': 'Distribution Center',
            'estimated_delivery': order.estimated_delivery_date.strftime('%Y-%m-%d') if order.estimated_delivery_date else 'TBD',
            'tracking_number': getattr(order, 'tracking_number', f"TRK{order.id:06d}"),
            'last_updated': order.status_updated_at.strftime('%Y-%m-%d %H:%M:%S') if order.status_updated_at else 'N/A',
            'delivery_progress': []
        }
        
        # Add progress steps based on status logs
        for log in reversed(latest_logs):
            tracking_info['delivery_progress'].append({
                'status': log.new_status,
                'timestamp': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'notes': log.notes or f'Order status updated to {log.new_status}'
            })
        
        return JsonResponse({
            'success': True,
            'tracking_info': tracking_info
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error getting tracking information: {str(e)}'
        })

@csrf_protect
def mark_order_delivered(request, order_id):
    """Mark an order as delivered"""
    # Check authentication for AJAX requests
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)
    
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized access'}, status=403)
    
    if request.method == 'POST':
        try:
            order = get_object_or_404(Orders, id=order_id)
            
            if order.status not in ['Out for Delivery']:
                return JsonResponse({
                    'success': False,
                    'message': 'Order must be "Out for Delivery" to mark as delivered'
                })
            
            # Update order status
            previous_status = order.status
            order.status = 'Delivered'
            order.status_updated_at = timezone.now()
            order.delivered_at = timezone.now()
            order.save()
            
            # Log the status change
            DeliveryStatusLog.objects.create(
                order=order,
                previous_status=previous_status,
                new_status='Delivered',
                updated_by=request.user.username,
                update_method='manual_delivery',
                notes='Order manually marked as delivered'
            )
            
            # Reduce inventory when order is marked as delivered
            order_items = order.orderitem_set.all()
            inventory_updates = []
            
            for order_item in order_items:
                try:
                    inventory_item = models.InventoryItem.objects.get(product=order_item.product)
                    if inventory_item.quantity >= order_item.quantity:
                        inventory_item.quantity -= order_item.quantity
                        inventory_item.save()
                        inventory_updates.append(f'{inventory_item.product.name}: -{order_item.quantity}')
                    else:
                        return JsonResponse({
                            'success': False,
                            'message': f'Insufficient inventory for {inventory_item.product.name}'
                        })
                except models.InventoryItem.DoesNotExist:
                    inventory_updates.append(f'{order_item.product.name}: No inventory item found')
            
            return JsonResponse({
                'success': True,
                'message': 'Order marked as delivered successfully',
                'inventory_updates': inventory_updates
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error marking order as delivered: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def delivery_status_page(request, token):
    """Public delivery status page accessible via magic link"""
    try:
        magic_link = get_object_or_404(DeliveryMagicLink, token=token, is_active=True)
        
        if magic_link.is_expired:
            return render(request, 'ecom/magic_link_expired.html', {
                'order': magic_link.order
            })
        
        order = magic_link.order
        order_items = order.orderitem_set.all()
        status_logs = order.status_logs.all()[:10]  # Last 10 status changes
        
        # Calculate order totals
        total_amount = sum(item.price * item.quantity for item in order_items)
        
        # Define available actions based on current status
        available_actions = []
        if order.status == 'Pending':
            available_actions = [
                {'action': 'confirm', 'label': 'Confirm Order', 'class': 'btn-success'}
            ]
        elif order.status == 'Processing':
            available_actions = [
                {'action': 'ship', 'label': 'Mark as Shipped', 'class': 'btn-primary'}
            ]
        elif order.status == 'Out for Delivery':
            available_actions = [
                {'action': 'deliver', 'label': 'Mark as Delivered', 'class': 'btn-success'}
            ]
        
        # Add cancel option for non-delivered orders
        if order.status not in ['Delivered', 'Cancelled']:
            available_actions.append({
                'action': 'cancel', 'label': 'Cancel Order', 'class': 'btn-danger'
            })
        
        context = {
            'order': order,
            'order_items': order_items,
            'status_logs': status_logs,
            'total_amount': total_amount,
            'magic_link': magic_link,
            'available_actions': available_actions
        }
        
        return render(request, 'ecom/delivery_status.html', context)
        
    except Exception as e:
        return render(request, 'ecom/magic_link_error.html', {
            'error': str(e)
        })


@login_required
def customer_confirm_received(request, order_id):
    """
    Handle customer confirmation of order receipt with photo proof
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        # Get the customer
        customer = models.Customer.objects.get(user_id=request.user.id)
        
        # Get the order and verify it belongs to the customer
        order = models.Orders.objects.get(id=order_id, customer=customer)
        
        # Check if order is in 'Delivered' status
        if order.status != 'Delivered':
            return JsonResponse({
                'success': False, 
                'message': 'Order must be marked as delivered before confirming receipt'
            })
        
        # Check if already confirmed
        if order.customer_received_at:
            return JsonResponse({
                'success': False, 
                'message': 'Order receipt has already been confirmed'
            })
        
        # Check if photo was uploaded
        if 'delivery_proof' not in request.FILES:
            return JsonResponse({
                'success': False, 
                'message': 'Delivery proof photo is required'
            })
        
        # Save the delivery proof photo and confirmation timestamp
        order.delivery_proof_photo = request.FILES['delivery_proof']
        order.customer_received_at = timezone.now()
        order.save()
        
        # Create a delivery status log entry
        notes = request.POST.get('notes', '').strip()
        log_notes = f"Customer confirmed receipt with photo proof."
        if notes:
            log_notes += f" Customer notes: {notes}"
        
        models.DeliveryStatusLog.objects.create(
            order=order,
            previous_status='Delivered',
            new_status='Delivered',
            updated_by=request.user,
            update_method='Customer Confirmation',
            notes=log_notes
        )
        
        return JsonResponse({
            'success': True, 
            'message': 'Order receipt confirmed successfully!'
        })
        
    except models.Customer.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Customer not found'
        })
    except models.Orders.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Order not found or does not belong to you'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        })
