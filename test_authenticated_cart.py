#!/usr/bin/env python3
"""
Test script to reproduce the cart submission error with proper authentication
"""
import requests
import json
from bs4 import BeautifulSoup

# Base URL for the Django server
BASE_URL = 'http://127.0.0.1:8000'

def test_authenticated_cart_submission():
    """Test cart submission with proper authentication"""
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    print("1. Getting login page to extract CSRF token...")
    login_page = session.get(f'{BASE_URL}/customerlogin')
    soup = BeautifulSoup(login_page.content, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
    print(f"   CSRF token: {csrf_token[:20]}...")
    
    # Test credentials - using existing user
    login_data = {
        'csrfmiddlewaretoken': csrf_token,
        'username': 'mersyeon',  # Using existing user
        'password': 'admin123'  # You may need to adjust this password
    }
    
    print("2. Attempting to login...")
    login_response = session.post(f'{BASE_URL}/customerlogin', data=login_data)
    
    if login_response.status_code == 200 and 'customerlogin' not in login_response.url:
        print("   ✓ Login successful")
    else:
        print("   ✗ Login failed - creating test user first...")
        # Try to register a test user
        register_page = session.get(f'{BASE_URL}/customersignup')
        soup = BeautifulSoup(register_page.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        
        register_data = {
            'csrfmiddlewaretoken': csrf_token,
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'mobile': '1234567890',
            'address': 'Test Address'
        }
        
        register_response = session.post(f'{BASE_URL}/customersignup', data=register_data)
        print(f"   Registration response: {register_response.status_code}")
        
        # Try login again
        login_page = session.get(f'{BASE_URL}/customerlogin')
        soup = BeautifulSoup(login_page.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        
        login_data['csrfmiddlewaretoken'] = csrf_token
        login_response = session.post(f'{BASE_URL}/customerlogin', data=login_data)
        
        if login_response.status_code == 200 and 'customerlogin' not in login_response.url:
            print("   ✓ Login successful after registration")
        else:
            print("   ✗ Login still failed")
            return
    
    print("3. Getting customizer page to extract CSRF token...")
    customizer_page = session.get(f'{BASE_URL}/customizer')
    soup = BeautifulSoup(customizer_page.content, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
    print(f"   CSRF token: {csrf_token[:20]}...")
    
    print("4. Preparing cart submission data...")
    cart_data = {
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
    
    print("5. Submitting cart data...")
    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token,
        'Referer': f'{BASE_URL}/customizer'
    }
    
    response = session.post(
        f'{BASE_URL}/api/add-custom-order/',
        json=cart_data,
        headers=headers
    )
    
    print(f"   Response status: {response.status_code}")
    print(f"   Response headers: {dict(response.headers)}")
    
    try:
        response_data = response.json()
        print(f"   Response data: {json.dumps(response_data, indent=2)}")
        
        if response_data.get('success'):
            print("   ✓ Cart submission successful!")
        else:
            print(f"   ✗ Cart submission failed: {response_data.get('message', 'Unknown error')}")
            
    except json.JSONDecodeError:
        print(f"   ✗ Invalid JSON response: {response.text[:500]}")
    
    print("\n6. Checking server logs for any error messages...")

if __name__ == '__main__':
    test_authenticated_cart_submission()