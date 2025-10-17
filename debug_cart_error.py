#!/usr/bin/env python3
"""
Debug script to test the add_custom_order function directly
"""
import os
import sys
import django
import json
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth.models import User
from ecom.models import Customer, CustomJerseyDesign, CustomOrderItem, Orders

def debug_add_custom_order():
    """Debug the add_custom_order function by testing its components"""
    
    print("=== Debugging Custom Order Creation ===")
    
    # Get an existing customer
    try:
        customer = Customer.objects.first()
        if not customer:
            print("❌ No customers found in database")
            return
        print(f"✓ Using customer: {customer.user.username}")
    except Exception as e:
        print(f"❌ Error getting customer: {e}")
        return
    
    # Test data similar to what would come from the frontend
    test_data = {
        'orderType': 'cart',
        'quantity': 1,
        'size': 'M',
        'additionalInfo': 'Test custom jersey order',
        'designConfig': {
            'jerseyType': 'standard',
            'primaryColor': '#ff0000',
            'secondaryColor': '#ffffff',
            'pattern': 'solid',
            'frontNumber': '10',
            'backName': 'TEST',
            'backNumber': '10',
            'textColor': '#000000',
            'logoPlacement': 'none'
        }
    }
    
    print(f"✓ Test data prepared: {json.dumps(test_data, indent=2)}")
    
    try:
        # Extract data like the view does
        order_type = test_data.get('orderType', 'cart')
        quantity = int(test_data.get('quantity', 1))
        size = test_data.get('size', 'M')
        additional_info = test_data.get('additionalInfo', '')
        design_config = test_data.get('designConfig', {})
        
        print(f"✓ Extracted order_type: {order_type}")
        print(f"✓ Extracted quantity: {quantity}")
        print(f"✓ Extracted size: {size}")
        print(f"✓ Extracted additional_info: {additional_info}")
        print(f"✓ Extracted design_config: {design_config}")
        
        # Validate size
        valid_sizes = ['XS', 'S', 'M', 'L', 'XL']
        if size not in valid_sizes:
            print(f"❌ Invalid size: {size}. Valid sizes: {valid_sizes}")
            return
        print(f"✓ Size validation passed")
        
        # Create CustomJerseyDesign
        print("Creating CustomJerseyDesign...")
        custom_design = CustomJerseyDesign.objects.create(
            customer=customer,
            jersey_type=design_config.get('jerseyType', 'standard'),
            primary_color=design_config.get('primaryColor', '#000000'),
            secondary_color=design_config.get('secondaryColor', '#ffffff'),
            pattern=design_config.get('pattern', 'solid'),
            front_number=design_config.get('frontNumber', ''),
            back_name=design_config.get('backName', ''),
            back_number=design_config.get('backNumber', ''),
            text_color=design_config.get('textColor', '#000000'),
            logo_placement=design_config.get('logoPlacement', 'none'),
            design_data=design_config
        )
        print(f"✓ CustomJerseyDesign created with ID: {custom_design.id}")
        
        # Set base price
        base_price = Decimal('599.00')
        print(f"✓ Base price set: {base_price}")
        
        if order_type == 'pre-order':
            print("Creating pre-order...")
            # Create a new order for pre-order
            order = Orders.objects.create(
                customer=customer,
                email=customer.user.email,
                address=customer.get_full_address,
                mobile=customer.mobile,
                status='Pending',
                payment_method='cod'
            )
            print(f"✓ Pre-order created with ID: {order.id}")
            
            # Create custom order item
            custom_item = CustomOrderItem.objects.create(
                order=order,
                custom_design=custom_design,
                quantity=quantity,
                size=size,
                price=base_price,
                additional_info=additional_info,
                is_pre_order=True
            )
            print(f"✓ Custom order item created with ID: {custom_item.id}")
            print(f"✓ Pre-order process completed successfully!")
            
        else:  # Add to cart
            print("Adding to cart...")
            # Check if customer has an existing pending cart order
            cart_order, created = Orders.objects.get_or_create(
                customer=customer,
                status='Pending',
                defaults={
                    'email': customer.user.email,
                    'address': customer.get_full_address,
                    'mobile': customer.mobile,
                    'payment_method': 'cod'
                }
            )
            print(f"✓ Cart order {'created' if created else 'found'} with ID: {cart_order.id}")
            
            # Create custom order item
            custom_item = CustomOrderItem.objects.create(
                order=cart_order,
                custom_design=custom_design,
                quantity=quantity,
                size=size,
                price=base_price,
                additional_info=additional_info,
                is_pre_order=False
            )
            print(f"✓ Custom cart item created with ID: {custom_item.id}")
            print(f"✓ Cart process completed successfully!")
            
    except Exception as e:
        print(f"❌ Error during custom order creation: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n=== Testing Complete - No Errors Found ===")

if __name__ == '__main__':
    debug_add_custom_order()