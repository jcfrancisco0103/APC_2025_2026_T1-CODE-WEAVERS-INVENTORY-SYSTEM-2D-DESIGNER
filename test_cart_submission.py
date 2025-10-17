#!/usr/bin/env python
"""
Simple test script to verify cart submission functionality
"""
import requests
import json

# Test the add-custom-order endpoint
url = 'http://127.0.0.1:8000/api/add-custom-order/'

# Test data
test_data = {
    'quantity': 1,
    'size': 'M',
    'additionalInfo': 'Test order',
    'designConfig': {'test': 'config'},
    'designImage': 'data:image/png;base64,test',
    'orderType': 'cart'
}

print("Testing cart submission endpoint...")
print(f"URL: {url}")
print(f"Data: {json.dumps(test_data, indent=2)}")

try:
    # First, get the CSRF token
    session = requests.Session()
    csrf_response = session.get('http://127.0.0.1:8000/customizer/')
    
    if csrf_response.status_code == 200:
        print("✓ Successfully accessed customizer page")
        
        # Extract CSRF token from response
        csrf_token = None
        if 'csrfmiddlewaretoken' in csrf_response.text:
            # Simple extraction - in real scenario, would parse HTML properly
            import re
            match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', csrf_response.text)
            if match:
                csrf_token = match.group(1)
                print(f"✓ CSRF token extracted: {csrf_token[:20]}...")
        
        if csrf_token:
            # Make the POST request with CSRF token
            headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token,
                'Referer': 'http://127.0.0.1:8000/customizer/'
            }
            
            response = session.post(url, json=test_data, headers=headers)
            
            print(f"\nResponse Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                print(f"Response Data: {json.dumps(response_data, indent=2)}")
            except:
                print(f"Response Text: {response.text[:500]}...")
                
        else:
            print("✗ Could not extract CSRF token")
    else:
        print(f"✗ Failed to access customizer page: {csrf_response.status_code}")

except Exception as e:
    print(f"✗ Error: {e}")

print("\nTest completed.")