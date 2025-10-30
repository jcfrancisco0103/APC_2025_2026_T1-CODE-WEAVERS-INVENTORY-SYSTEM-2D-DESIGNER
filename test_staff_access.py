#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from ecom.models import SuperAdmin

def test_staff_access_restrictions():
    print("=== Testing Staff Access Restrictions ===")
    
    # Create test client
    client = Client()
    
    # Create a Staff user (is_staff=True but no SuperAdmin record)
    try:
        # Try to get existing staff user or create new one
        try:
            staff_user = User.objects.get(username='teststaff')
            print(f"Using existing staff user: {staff_user.username}")
        except User.DoesNotExist:
            staff_user = User.objects.create_user(
                username='teststaff',
                email='teststaff@example.com',
                password='testpass123',
                is_staff=True,  # Staff user
                is_active=True
            )
            print(f"Created new staff user: {staff_user.username}")
        
        # Verify this user is NOT a SuperAdmin
        try:
            superadmin_record = staff_user.superadmin
            print(f"WARNING: Staff user has SuperAdmin record: {superadmin_record}")
        except SuperAdmin.DoesNotExist:
            print("✓ Staff user has no SuperAdmin record (correct)")
        
        # Test login
        print("\n=== Testing Staff User Login ===")
        login_success = client.login(username='teststaff', password='testpass123')
        print(f"Staff login successful: {login_success}")
        
        if login_success:
            print("\n=== Testing SuperAdmin Page Access ===")
            
            # Test SuperAdmin dashboard (should be denied)
            response = client.get('/superadmin-dashboard/')
            print(f"SuperAdmin Dashboard: {response.status_code}")
            if response.status_code == 302:
                print("  ✓ Access denied (redirected) - CORRECT")
            elif response.status_code == 200:
                print("  ✗ Access allowed - INCORRECT!")
            else:
                print(f"  ? Unexpected status: {response.status_code}")
            
            # Test manage users (should be denied)
            response = client.get('/manage-users/')
            print(f"Manage Users: {response.status_code}")
            if response.status_code == 302:
                print("  ✓ Access denied (redirected) - CORRECT")
            elif response.status_code == 200:
                print("  ✗ Access allowed - INCORRECT!")
            else:
                print(f"  ? Unexpected status: {response.status_code}")
            
            # Test create staff (should be denied)
            response = client.get('/create-staff/')
            print(f"Create Staff: {response.status_code}")
            if response.status_code == 302:
                print("  ✓ Access denied (redirected) - CORRECT")
            elif response.status_code == 200:
                print("  ✗ Access allowed - INCORRECT!")
            else:
                print(f"  ? Unexpected status: {response.status_code}")
            
            # Test regular admin dashboard (should be allowed) - fix URL
            response = client.get('/admin-dashboard')
            print(f"Admin Dashboard: {response.status_code}")
            if response.status_code == 200:
                print("  ✓ Access allowed - CORRECT")
                # Check if SuperAdmin navigation is hidden for Staff users
                if b'SuperAdmin Dashboard' in response.content:
                    print("  ✗ SuperAdmin navigation visible to Staff - INCORRECT!")
                else:
                    print("  ✓ SuperAdmin navigation hidden from Staff - CORRECT")
            else:
                print(f"  ? Unexpected status: {response.status_code}")
        else:
            print("Staff login failed - cannot test pages")
            
    except Exception as e:
        print(f"Error during testing: {e}")

def test_superadmin_access():
    print("\n=== Testing SuperAdmin Access (for comparison) ===")
    
    client = Client()
    
    # Get a SuperAdmin user
    try:
        superadmin_users = User.objects.filter(superadmin__isnull=False, superadmin__is_active=True)
        if superadmin_users.exists():
            superadmin_user = superadmin_users.first()
            print(f"Testing with SuperAdmin: {superadmin_user.username}")
            
            # Note: We can't test login without knowing the password
            # But we can check if the user has SuperAdmin record
            try:
                superadmin_record = superadmin_user.superadmin
                print(f"✓ SuperAdmin record found: {superadmin_record.employee_id}")
            except:
                print("✗ No SuperAdmin record found")
        else:
            print("No SuperAdmin users found")
    except Exception as e:
        print(f"Error testing SuperAdmin: {e}")

if __name__ == "__main__":
    test_staff_access_restrictions()
    test_superadmin_access()