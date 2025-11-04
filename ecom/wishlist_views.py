# Wishlist and Review functionality
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.http import require_GET
from django.db.models import Q, Avg
from . import models

def is_customer(user):
    return user.groups.filter(name='CUSTOMER').exists()

# Wishlist functionality
@login_required
@user_passes_test(is_customer)
@csrf_protect
def add_to_wishlist(request, product_id):
    if request.method == 'POST':
        try:
            customer = models.Customer.objects.get(user=request.user)
            product = models.Product.objects.get(id=product_id)
            
            wishlist_item, created = models.Wishlist.objects.get_or_create(
                customer=customer,
                product=product
            )
            
            if created:
                return JsonResponse({'success': True, 'message': 'Product added to wishlist'})
            else:
                return JsonResponse({'success': True, 'message': 'Product already in wishlist'})
                
        except (models.Customer.DoesNotExist, models.Product.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Product or customer not found'}, status=404)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

@login_required
@user_passes_test(is_customer)
@csrf_protect
def remove_from_wishlist(request, product_id):
    if request.method == 'POST':
        try:
            customer = models.Customer.objects.get(user=request.user)
            wishlist_item = models.Wishlist.objects.get(customer=customer, product_id=product_id)
            wishlist_item.delete()
            return JsonResponse({'success': True, 'message': 'Product removed from wishlist'})
        except (models.Customer.DoesNotExist, models.Wishlist.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Wishlist item not found'}, status=404)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

@login_required
@user_passes_test(is_customer)
def wishlist_view(request):
    try:
        customer = models.Customer.objects.get(user=request.user)
        wishlist_items = models.Wishlist.objects.filter(customer=customer).select_related('product')
        
        # If it's an AJAX request, return JSON data
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            wishlist_product_ids = [item.product.id for item in wishlist_items]
            return JsonResponse({
                'success': True,
                'wishlist_items': wishlist_product_ids,
                'total_items': len(wishlist_product_ids)
            })
        
        # Cart count logic
        if 'product_ids' in request.COOKIES:
            product_ids = request.COOKIES['product_ids']
            counter = product_ids.split('|')
            product_count_in_cart = len(set(counter))
        else:
            product_count_in_cart = 0
        
        context = {
            'wishlist_items': wishlist_items,
            'product_count_in_cart': product_count_in_cart,
            'total_items': wishlist_items.count(),
        }
        return render(request, 'ecom/wishlist.html', context)
    except models.Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found.')
        return redirect('customer-home')

# Product Review functionality
@login_required
@user_passes_test(is_customer)
def add_review(request, product_id):
    if request.method == 'POST':
        try:
            customer = models.Customer.objects.get(user=request.user)
            product = models.Product.objects.get(id=product_id)
            
            # Check if customer has purchased and received (Delivered) this product
            # via OrderItem entries linked to Orders
            has_purchased = models.OrderItem.objects.filter(
                order__customer=customer,
                product=product,
                order__status__in=['Delivered', 'Completed']
            ).exists()
            
            if not has_purchased:
                return JsonResponse({'status': 'error', 'message': 'You can only review products you have purchased'}, status=400)
            
            rating = int(request.POST.get('rating'))
            review_text = request.POST.get('review_text', '')
            
            review, created = models.ProductReview.objects.update_or_create(
                customer=customer,
                product=product,
                defaults={
                    'rating': rating,
                    'review_text': review_text
                }
            )
            
            action = 'added' if created else 'updated'
            return JsonResponse({'status': 'success', 'message': f'Review {action} successfully'})
            
        except (models.Customer.DoesNotExist, models.Product.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Product or customer not found'}, status=404)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid rating value'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
@user_passes_test(is_customer)
def product_detail_view(request, product_id):
    try:
        product = models.Product.objects.get(id=product_id)
        
        # Get product reviews
        reviews = models.ProductReview.objects.filter(product=product).select_related('customer__user').order_by('-created_at')
        
        # Calculate average rating
        avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        if avg_rating:
            avg_rating = round(avg_rating, 1)
        
        # Check if current user has this product in wishlist
        in_wishlist = False
        user_review = None
        wishlist_product_ids = []
        can_review = False
        review_mode = False
        purchased_size = None
        purchased_quantity = None
        if request.user.is_authenticated and is_customer(request.user):
            try:
                customer = models.Customer.objects.get(user=request.user)
                in_wishlist = models.Wishlist.objects.filter(customer=customer, product=product).exists()
                # Get all wishlist product IDs for related products
                wishlist_items = models.Wishlist.objects.filter(customer=customer)
                wishlist_product_ids = [item.product.id for item in wishlist_items]
                try:
                    user_review = models.ProductReview.objects.get(customer=customer, product=product)
                except models.ProductReview.DoesNotExist:
                    pass
                # Determine if user can review: must have delivered order item for this product
                can_review = models.OrderItem.objects.filter(
                    order__customer=customer,
                    product=product,
                    order__status__in=['Delivered', 'Completed']
                ).exists()

                # Detect review mode via query params and pull purchased variant details
                from_param = request.GET.get('from')
                if from_param == 'review' and can_review:
                    review_mode = True
                    order_item_id = request.GET.get('order_item_id')
                    order_item_qs = models.OrderItem.objects.filter(
                        order__customer=customer,
                        product=product,
                        order__status__in=['Delivered', 'Completed']
                    )
                    if order_item_id:
                        order_item_qs = order_item_qs.filter(id=order_item_id)
                    order_item = order_item_qs.order_by('-id').first()
                    if order_item:
                        purchased_size = order_item.size
                        purchased_quantity = order_item.quantity
            except models.Customer.DoesNotExist:
                pass
        
        # Cart count logic
        if 'product_ids' in request.COOKIES:
            product_ids = request.COOKIES['product_ids']
            counter = product_ids.split('|')
            product_count_in_cart = len(set(counter))
        else:
            product_count_in_cart = 0
        
        # Get related products (random selection)
        related_products = models.Product.objects.exclude(id=product.id).order_by('?')[:4]
        
        context = {
            'product': product,
            'reviews': reviews,
            'avg_rating': avg_rating,
            'review_count': reviews.count(),
            'in_wishlist': in_wishlist,
            'user_review': user_review,
            'product_count_in_cart': product_count_in_cart,
            'related_products': related_products,
            'wishlist_product_ids': wishlist_product_ids,
            'can_review': can_review,
            'review_mode': review_mode,
            'purchased_size': purchased_size,
            'purchased_quantity': purchased_quantity,
        }
        return render(request, 'ecom/product_detail.html', context)
        
    except models.Product.DoesNotExist:
        messages.error(request, 'Product not found.')
        return redirect('customer-home')


@login_required
@user_passes_test(is_customer)
def product_reviews_api(request, product_id):
    try:
        product = models.Product.objects.get(id=product_id)

        reviews = (
            models.ProductReview.objects
            .filter(product=product)
            .select_related('customer__user')
            .order_by('-created_at')
        )

        results = []
        for r in reviews:
            order_item = (
                models.OrderItem.objects
                .filter(
                    order__customer=r.customer,
                    product=product,
                    order__status__in=['Delivered', 'Completed']
                )
                .order_by('-id')
                .first()
            )

            customer_name = (r.customer.user.first_name or r.customer.user.username)
            if r.customer.user.last_name:
                customer_name = f"{customer_name} {r.customer.user.last_name}"

            results.append({
                'customer_name': customer_name.strip(),
                'rating': r.rating,
                'review_text': r.review_text or '',
                'created_at': r.created_at.strftime('%Y-%m-%d %H:%M'),
                'size': getattr(order_item, 'size', None),
                'quantity': getattr(order_item, 'quantity', None),
            })

        return JsonResponse({
            'status': 'success',
            'product_id': product.id,
            'reviews': results,
        })
    except models.Product.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)

# Newsletter functionality
@csrf_protect
def newsletter_signup(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            newsletter, created = models.Newsletter.objects.get_or_create(email=email)
            if created:
                return JsonResponse({'status': 'success', 'message': 'Successfully subscribed to newsletter'})
            else:
                return JsonResponse({'status': 'info', 'message': 'Email already subscribed'})
        return JsonResponse({'status': 'error', 'message': 'Email is required'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

# Enhanced search API
@require_GET
def search_products_api(request):
    query = request.GET.get('q', '')

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    products = models.Product.objects.all()
    
    if query:
        search_words = query.split()
        search_query = Q()
        
        for word in search_words:
            search_query |= (
                Q(name__icontains=word) | 
                Q(description__icontains=word)
            )
        
        products = products.filter(search_query).distinct()
    

    
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
    
    # Limit results for API
    products = products[:20]
    
    products_data = []
    for product in products:
        products_data.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),

            'image_url': product.product_image.url if product.product_image else None,
        })
    
    return JsonResponse({'products': products_data})
