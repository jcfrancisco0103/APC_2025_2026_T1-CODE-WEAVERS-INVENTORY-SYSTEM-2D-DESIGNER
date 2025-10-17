#!/usr/bin/env python3
"""
Test script to directly call the add-custom-order API and trigger error logging
"""
import requests
import json

# Base URL for the Django server
BASE_URL = 'http://127.0.0.1:8000'

def test_direct_api_call():
    """Test the API endpoint directly to trigger error logging"""
    
    print("Testing direct API call to /api/add-custom-order/")
    
    # Test data
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
    
    print("Sending POST request...")
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/add-custom-order/',
            json=cart_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response data: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Raw response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == '__main__':
    test_direct_api_call()