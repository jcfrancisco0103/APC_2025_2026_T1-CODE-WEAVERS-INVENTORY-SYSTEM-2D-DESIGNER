#!/usr/bin/env python
"""
Test script to verify that the sleeve_type field fix resolves the NOT NULL constraint error.
"""
import requests
import json

def test_add_to_cart():
    """Test the add-to-cart functionality with the new sleeve_type field."""
    
    # Test data that should work with the new sleeve_type field
    test_data = {
        'jersey_type': 'jersey',
        'collar_type': 'crew_neck', 
        'sleeve_type': 'short_sleeve',
        'primary_color': '#FF0000',
        'secondary_color': '#0000FF',
        'pattern': 'solid',
        'front_number': '10',
        'back_name': 'TEST',
        'back_number': '10',
        'text_color': '#FFFFFF',
        'logo_placement': 'center',
        'design_scale': 1.0,
        'fabric_type': 'polyester',
        'is_3d_design': True,
        'logo_position_3d': {'x': 0, 'y': 0, 'z': 0},
        'design_data': json.dumps({'test': 'data'}),
        'size': 'M',
        'quantity': 1
    }
    
    try:
        # Make request to add custom t-shirt to cart
        response = requests.post(
            'http://127.0.0.1:8000/api/add-custom-tshirt-to-cart/',
            data=test_data,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Add to cart functionality is working!")
            return True
        else:
            print("❌ FAILED: Add to cart returned an error")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Testing add-to-cart functionality with sleeve_type field fix...")
    print("=" * 60)
    
    success = test_add_to_cart()
    
    print("=" * 60)
    if success:
        print("🎉 All tests passed! The sleeve_type field fix is working correctly.")
    else:
        print("💥 Tests failed. There may still be issues with the implementation.")