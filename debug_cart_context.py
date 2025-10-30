#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from ecom import models
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.contrib.auth import authenticate
from ecom.views import cart_view

def debug_cart_context():
    print("=== DEBUGGING CART CONTEXT ===")
    
    # Create a request factory
    factory = RequestFactory()
    
    # Test with different users
    users_to_test = ['kurtyuri1130', 'mersyeon0103', 'rainerlopez0103']
    
    for username in users_to_test:
        try:
            user = User.objects.get(username=username)
            print(f"\n--- Testing user: {username} ---")
            
            # Create a mock request
            request = factory.get('/cart')
            request.user = user
            
            # Check if user has customer profile
            try:
                customer = models.Customer.objects.get(user=user)
                print(f"Customer ID: {customer.id}")
                
                # Check pending orders
                cart_orders = models.Orders.objects.filter(
                    customer=customer,
                    status='Pending'
                )
                print(f"Pending orders: {cart_orders.count()}")
                
                custom_items = []
                total = 0
                
                for cart_order in cart_orders:
                    custom_order_items = models.CustomOrderItem.objects.filter(
                        order=cart_order,
                        is_pre_order=False
                    )
                    print(f"  Order {cart_order.id}: {custom_order_items.count()} custom items")
                    
                    for item in custom_order_items:
                        item_total = item.price * item.quantity
                        total += item_total
                        custom_items.append({
                            'custom_item': item,
                            'size': item.size,
                            'quantity': item.quantity,
                            'price': item.price,
                            'total': item_total
                        })
                        print(f"    Item: Size {item.size}, Qty {item.quantity}, Price {item.price}")
                
                print(f"Total custom items: {len(custom_items)}")
                print(f"Total value: {total}")
                
                # Test if the cart view would work
                print("Testing cart view function...")
                try:
                    # This won't work completely because we need cookies, but we can see if it crashes
                    response = cart_view(request)
                    print(f"Cart view response status: {response.status_code}")
                except Exception as e:
                    print(f"Cart view error: {e}")
                
            except models.Customer.DoesNotExist:
                print("No customer profile found")
                
        except User.DoesNotExist:
            print(f"User {username} not found")
    
    # Check if there are any custom items at all
    print(f"\n=== OVERALL STATISTICS ===")
    all_custom_items = models.CustomOrderItem.objects.all()
    print(f"Total custom order items in database: {all_custom_items.count()}")
    
    pending_custom_items = models.CustomOrderItem.objects.filter(
        order__status='Pending',
        is_pre_order=False
    )
    print(f"Pending custom order items: {pending_custom_items.count()}")
    
    for item in pending_custom_items:
        print(f"  Item {item.id}: Customer {item.order.customer.user.username}, Size {item.size}, Qty {item.quantity}")

if __name__ == "__main__":
    debug_cart_context()