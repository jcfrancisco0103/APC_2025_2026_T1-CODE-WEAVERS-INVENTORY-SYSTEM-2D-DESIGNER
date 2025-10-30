#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from ecom.models import SuperAdmin

def test_superadmin_functionality():
    print("=== Testing SuperAdmin Functionality ===")
    
    # Create test client
    client = Client()
    
    # Get a SuperAdmin user
    try:
        superadmin_user = User.objects.get(username='testadmin')
        print(f"Testing with user: {superadmin_user.username}")
        
        # Check if user has SuperAdmin record
        try:
            superadmin_record = superadmin_user.superadmin
            print(f"SuperAdmin record found: {superadmin_record.employee_id} (active: {superadmin_record.is_active})")
        except:
            print("No SuperAdmin record found for this user")
            return
        
        # Try to login
        print("\n=== Testing Login ===")
        login_success = client.login(username='testadmin', password='testpass123')
        print(f"Login successful: {login_success}")
        
        if login_success:
            print("\n=== Testing SuperAdmin Pages ===")
            
            # Test SuperAdmin dashboard
            response = client.get('/superadmin-dashboard/')
            print(f"SuperAdmin Dashboard: {response.status_code}")
            if response.status_code != 200:
                print(f"  Error: {response.content.decode()[:200]}...")
            
            # Test manage users
            response = client.get('/manage-users/')
            print(f"Manage Users: {response.status_code}")
            if response.status_code != 200:
                print(f"  Error: {response.content.decode()[:200]}...")
            
            # Test create superadmin
            response = client.get('/create-superadmin/')
            print(f"Create SuperAdmin: {response.status_code}")
            if response.status_code != 200:
                print(f"  Error: {response.content.decode()[:200]}...")
        else:
            print("Login failed - cannot test pages")
            
    except User.DoesNotExist:
        print("SuperAdmin test user not found")
        
        # List available SuperAdmin users
        superadmin_users = User.objects.filter(superadmin__isnull=False)
        print(f"Available SuperAdmin users: {[u.username for u in superadmin_users]}")

if __name__ == "__main__":
    test_superadmin_functionality()