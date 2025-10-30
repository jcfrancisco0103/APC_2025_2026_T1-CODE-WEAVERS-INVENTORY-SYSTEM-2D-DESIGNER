#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from ecom.models import SuperAdmin

def test_superadmin_access():
    print("=== Testing SuperAdmin Access ===")
    
    client = Client()
    
    # Get SuperAdmin user
    try:
        superadmin_users = User.objects.filter(superadmin__isnull=False, superadmin__is_active=True)
        if superadmin_users.exists():
            superadmin_user = superadmin_users.first()
            print(f"Testing with SuperAdmin: {superadmin_user.username}")
            
            # We'll test by checking the context processor directly
            from ecom.context_processors import superadmin_context
            from django.http import HttpRequest
            
            # Create a mock request with the SuperAdmin user
            request = HttpRequest()
            request.user = superadmin_user
            
            context = superadmin_context(request)
            print(f"Context processor result: {context}")
            
            if context.get('is_superadmin'):
                print("✓ SuperAdmin correctly identified by context processor")
            else:
                print("✗ SuperAdmin NOT identified by context processor - PROBLEM!")
                
        else:
            print("No SuperAdmin users found")
    except Exception as e:
        print(f"Error testing SuperAdmin: {e}")

def test_staff_access():
    print("\n=== Testing Staff Access ===")
    
    client = Client()
    
    # Get or create Staff user
    try:
        try:
            staff_user = User.objects.get(username='teststaff')
        except User.DoesNotExist:
            staff_user = User.objects.create_user(
                username='teststaff',
                email='teststaff@example.com',
                password='testpass123',
                is_staff=True,
                is_active=True
            )
        
        print(f"Testing with Staff user: {staff_user.username}")
        
        # Test context processor
        from ecom.context_processors import superadmin_context
        from django.http import HttpRequest
        
        request = HttpRequest()
        request.user = staff_user
        
        context = superadmin_context(request)
        print(f"Context processor result: {context}")
        
        if not context.get('is_superadmin'):
            print("✓ Staff user correctly NOT identified as SuperAdmin")
        else:
            print("✗ Staff user incorrectly identified as SuperAdmin - PROBLEM!")
            
        # Test actual page access
        login_success = client.login(username='teststaff', password='testpass123')
        if login_success:
            print("✓ Staff login successful")
            
            # Test admin dashboard access
            response = client.get('/admin-dashboard')
            if response.status_code == 200:
                print("✓ Staff can access admin dashboard")
                
                # Check navigation content
                if b'SuperAdmin Dashboard' in response.content:
                    print("✗ SuperAdmin navigation visible to Staff - PROBLEM!")
                else:
                    print("✓ SuperAdmin navigation hidden from Staff")
            else:
                print(f"✗ Staff cannot access admin dashboard: {response.status_code}")
                
            # Test SuperAdmin page access (should be denied)
            response = client.get('/superadmin-dashboard/')
            if response.status_code == 302:
                print("✓ Staff correctly denied access to SuperAdmin dashboard")
            else:
                print(f"✗ Staff access to SuperAdmin dashboard: {response.status_code}")
        else:
            print("✗ Staff login failed")
            
    except Exception as e:
        print(f"Error testing Staff: {e}")

def test_regular_user_access():
    print("\n=== Testing Regular User Access ===")
    
    client = Client()
    
    # Get or create regular user
    try:
        try:
            regular_user = User.objects.get(username='testregular')
        except User.DoesNotExist:
            regular_user = User.objects.create_user(
                username='testregular',
                email='testregular@example.com',
                password='testpass123',
                is_staff=False,
                is_active=True
            )
        
        print(f"Testing with Regular user: {regular_user.username}")
        
        # Test context processor
        from ecom.context_processors import superadmin_context
        from django.http import HttpRequest
        
        request = HttpRequest()
        request.user = regular_user
        
        context = superadmin_context(request)
        print(f"Context processor result: {context}")
        
        if not context.get('is_superadmin'):
            print("✓ Regular user correctly NOT identified as SuperAdmin")
        else:
            print("✗ Regular user incorrectly identified as SuperAdmin - PROBLEM!")
            
        # Test page access
        login_success = client.login(username='testregular', password='testpass123')
        if login_success:
            print("✓ Regular user login successful")
            
            # Test admin dashboard access (should be denied for regular users)
            response = client.get('/admin-dashboard')
            if response.status_code in [302, 403, 404]:
                print("✓ Regular user correctly denied access to admin dashboard")
            else:
                print(f"✗ Regular user has access to admin dashboard: {response.status_code}")
        else:
            print("✗ Regular user login failed")
            
    except Exception as e:
        print(f"Error testing Regular user: {e}")

if __name__ == "__main__":
    test_superadmin_access()
    test_staff_access()
    test_regular_user_access()
    print("\n=== Test Summary ===")
    print("Check the results above to ensure:")
    print("1. SuperAdmin users can see SuperAdmin navigation")
    print("2. Staff users can access admin but NOT see SuperAdmin navigation")
    print("3. Regular users cannot access admin areas")