#!/usr/bin/env python
import os
import sys
import django
import requests
from requests.auth import HTTPBasicAuth

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from ecom import models
from django.contrib.auth.models import User

def test_cart_view():
    print("=== TESTING CART VIEW ===")
    
    # Test the cart endpoint directly
    base_url = "http://127.0.0.1:8000"
    cart_url = f"{base_url}/cart"
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # First, get the login page to get CSRF token
    login_page = session.get(f"{base_url}/customerlogin")
    print(f"Login page status: {login_page.status_code}")
    
    # Try to access cart without login
    cart_response = session.get(cart_url)
    print(f"Cart access without login: {cart_response.status_code}")
    print(f"Response URL: {cart_response.url}")
    
    # Check if we're redirected to login
    if "login" in cart_response.url:
        print("Redirected to login page as expected")
    
    print("\n=== CHECKING SPECIFIC USER CART DATA ===")
    
    # Let's check what a specific user with pending items should see
    user = User.objects.get(username='kurtyuri1130')  # This user has pending items
    customer = models.Customer.objects.get(user=user)
    
    print(f"Checking cart for user: {user.username}")
    print(f"Customer ID: {customer.id}")
    
    # Get pending orders
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
        print(f"Order {cart_order.id}: {custom_order_items.count()} custom items")
        
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
            print(f"  Item: Size {item.size}, Qty {item.quantity}, Price {item.price}")
    
    print(f"Total custom items that should appear in cart: {len(custom_items)}")
    print(f"Total value: {total}")

if __name__ == "__main__":
    test_cart_view()