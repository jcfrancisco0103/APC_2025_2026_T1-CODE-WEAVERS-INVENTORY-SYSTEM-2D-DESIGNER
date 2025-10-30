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

def debug_cart_items():
    print("=== DEBUGGING CART ITEMS ===")
    
    # Get all users
    users = User.objects.all()
    print(f"Total users: {users.count()}")
    
    for user in users:
        print(f"\n--- User: {user.username} (ID: {user.id}) ---")
        
        # Check if user has customer profile
        try:
            customer = models.Customer.objects.get(user=user)
            print(f"Customer ID: {customer.id}")
            
            # Check pending orders
            pending_orders = models.Orders.objects.filter(
                customer=customer,
                status='Pending'
            )
            print(f"Pending orders: {pending_orders.count()}")
            
            for order in pending_orders:
                print(f"  Order ID: {order.id}, Ref: {order.order_ref}")
                
                # Check custom order items
                custom_items = models.CustomOrderItem.objects.filter(
                    order=order,
                    is_pre_order=False
                )
                print(f"  Custom items in this order: {custom_items.count()}")
                
                for item in custom_items:
                    print(f"    Item ID: {item.id}, Size: {item.size}, Qty: {item.quantity}, Price: {item.price}")
                    print(f"    Custom Design ID: {item.custom_design.id}")
                    
        except models.Customer.DoesNotExist:
            print("  No customer profile found")
    
    # Check all custom jersey designs
    print(f"\n=== ALL CUSTOM JERSEY DESIGNS ===")
    designs = models.CustomJerseyDesign.objects.all()
    print(f"Total custom designs: {designs.count()}")
    
    for design in designs:
        print(f"Design ID: {design.id}, Customer: {design.customer.user.username}")
        print(f"  Colors: {design.primary_color}, {design.secondary_color}")
        print(f"  Text: Front#{design.front_number}, Back#{design.back_number}, Name: {design.back_name}")
    
    # Check all custom order items
    print(f"\n=== ALL CUSTOM ORDER ITEMS ===")
    custom_items = models.CustomOrderItem.objects.all()
    print(f"Total custom order items: {custom_items.count()}")
    
    for item in custom_items:
        print(f"Item ID: {item.id}, Order: {item.order.id}, Status: {item.order.status}")
        print(f"  Size: {item.size}, Qty: {item.quantity}, Price: {item.price}")

if __name__ == "__main__":
    debug_cart_items()