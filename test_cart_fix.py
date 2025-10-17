#!/usr/bin/env python3
"""
Test script to verify the cart submission fix works correctly.
Tests both authenticated and unauthenticated scenarios.
"""

import requests
import json
from bs4 import BeautifulSoup

BASE_URL = "http://127.0.0.1:8000"

def get_csrf_token(session):
    """Get CSRF token from the customizer page"""
    response = session.get(f"{BASE_URL}/customizer")
    soup = BeautifulSoup(response.content, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    if csrf_token:
        return csrf_token.get('value')
    return None

def test_unauthenticated_cart_submission():
    """Test cart submission when user is not authenticated"""
    print("=== Testing Unauthenticated Cart Submission ===")
    
    session = requests.Session()
    csrf_token = get_csrf_token(session)
    
    if not csrf_token:
        print("❌ Could not get CSRF token")
        return False
    
    print(f"✓ Got CSRF token: {csrf_token[:20]}...")
    
    # Sample cart data
    cart_data = {
        "design_data": {
            "front_text": "TEST",
            "back_text": "PLAYER",
            "front_number": "10",
            "back_number": "10",
            "primary_color": "#FF0000",
            "secondary_color": "#FFFFFF"
        },
        "quantity": 1,
        "size": "M",
        "price": 500
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token,
        'Referer': f'{BASE_URL}/customizer'
    }
    
    try:
        response = session.post(
            f"{BASE_URL}/api/add-custom-order/",
            data=json.dumps(cart_data),
            headers=headers
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        # Check if response is HTML (redirect to login)
        if 'text/html' in response.headers.get('content-type', ''):
            print("✓ Correctly redirected to login page (HTML response)")
            return True
        else:
            try:
                response_data = response.json()
                print(f"JSON Response: {response_data}")
                # The API now correctly returns a JSON response with login redirect
                if (response_data.get('success') == False and 
                    'login' in response_data.get('message', '').lower() and
                    response_data.get('redirect') == '/customerlogin'):
                    print("✓ Correctly returned authentication error with redirect")
                    return True
                else:
                    print("❌ Unexpected JSON response for unauthenticated user")
                    return False
            except json.JSONDecodeError:
                print(f"❌ Could not parse response: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"❌ Error during request: {e}")
        return False

def test_authenticated_cart_submission():
    """Test cart submission when user is authenticated"""
    print("\n=== Testing Authenticated Cart Submission ===")
    
    session = requests.Session()
    
    # First get login page to get CSRF token
    login_page = session.get(f"{BASE_URL}/login")
    soup = BeautifulSoup(login_page.content, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    
    if not csrf_token:
        print("❌ Could not get CSRF token from login page")
        return False
    
    csrf_value = csrf_token.get('value')
    print(f"✓ Got login CSRF token: {csrf_value[:20]}...")
    
    # Try to login with existing user
    login_data = {
        'username': 'mersyeon',
        'password': 'admin123',
        'csrfmiddlewaretoken': csrf_value
    }
    
    login_response = session.post(f"{BASE_URL}/login", data=login_data)
    
    if login_response.status_code == 200 and 'login' not in login_response.url.lower():
        print("✓ Successfully logged in")
        
        # Now test cart submission
        csrf_token = get_csrf_token(session)
        if not csrf_token:
            print("❌ Could not get CSRF token after login")
            return False
        
        cart_data = {
            "design_data": {
                "front_text": "TEST",
                "back_text": "PLAYER", 
                "front_number": "10",
                "back_number": "10",
                "primary_color": "#FF0000",
                "secondary_color": "#FFFFFF"
            },
            "quantity": 1,
            "size": "M",
            "price": 500
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token,
            'Referer': f'{BASE_URL}/customizer'
        }
        
        try:
            response = session.post(
                f"{BASE_URL}/api/add-custom-order/",
                data=json.dumps(cart_data),
                headers=headers
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"JSON Response: {response_data}")
                    if response_data.get('success') == True:
                        print("✓ Cart submission successful!")
                        return True
                    else:
                        print(f"❌ Cart submission failed: {response_data.get('message')}")
                        return False
                except json.JSONDecodeError:
                    print(f"❌ Could not parse response: {response.text[:200]}")
                    return False
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error during cart submission: {e}")
            return False
    else:
        print("❌ Login failed")
        return False

def main():
    """Run all tests"""
    print("Testing Cart Submission Fix")
    print("=" * 50)
    
    # Test unauthenticated scenario
    unauthenticated_result = test_unauthenticated_cart_submission()
    
    # Test authenticated scenario  
    authenticated_result = test_authenticated_cart_submission()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"Unauthenticated test: {'✓ PASS' if unauthenticated_result else '❌ FAIL'}")
    print(f"Authenticated test: {'✓ PASS' if authenticated_result else '❌ FAIL'}")
    
    if unauthenticated_result and authenticated_result:
        print("\n🎉 All tests passed! Cart submission fix is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()