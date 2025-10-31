#!/usr/bin/env python3
"""
Simple test to check what happens when accessing protected URLs
"""

import requests

BASE_URL = "http://127.0.0.1:8000"

def test_url_access(url, description):
    """Test access to a specific URL"""
    try:
        response = requests.get(f"{BASE_URL}{url}")
        print(f"\n{description}:")
        print(f"  URL: {BASE_URL}{url}")
        print(f"  Status Code: {response.status_code}")
        print(f"  Content Length: {len(response.text)}")
        
        # Check if it's a redirect
        if response.history:
            print(f"  Redirected from: {response.history[0].url}")
            print(f"  Final URL: {response.url}")
        
        # Check for login form or admin content
        if 'login' in response.text.lower():
            print("  ✓ Contains login form (likely redirected to login)")
        elif 'dashboard' in response.text.lower():
            print("  ⚠️ Contains dashboard content (possible security issue)")
        elif 'admin' in response.text.lower():
            print("  ⚠️ Contains admin content (possible security issue)")
        else:
            print("  ? Unknown content type")
            
        # Show first 200 characters of response
        print(f"  Preview: {response.text[:200]}...")
        
    except Exception as e:
        print(f"\n{description}: ERROR - {e}")

if __name__ == "__main__":
    print("🔍 SIMPLE URL ACCESS TEST")
    print("=" * 50)
    
    # Test protected URLs
    test_url_access("/admin-dashboard", "Admin Dashboard")
    test_url_access("/superadmin-dashboard/", "SuperAdmin Dashboard")
    test_url_access("/manage-users/", "Manage Users")
    test_url_access("/create-staff/", "Create Staff")
    
    # Test public URLs for comparison
    test_url_access("/", "Home Page")
    test_url_access("/adminlogin", "Admin Login")