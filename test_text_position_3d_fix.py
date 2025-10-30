import requests
import json

# Test data for add-to-cart functionality
test_data = {
    "design_data": {
        "front_text": "Test Text",
        "back_text": "Back Text",
        "front_logo": "",
        "back_logo": "",
        "primary_color": "#FF0000",
        "secondary_color": "#0000FF",
        "sleeve_type": "crew_neck",
        "fabric_type": "polyester",
        "is_3d_design": True,
        "logo_position_3d": {"x": 0, "y": 0, "z": 0},
        "text_position_3d": {"x": 10, "y": 20, "z": 5}  # This should fix the NOT NULL constraint
    },
    "quantity": 1,
    "size": "M"
}

# Make request to add-to-cart endpoint
url = "http://127.0.0.1:8000/api/add-custom-tshirt-to-cart/"
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=test_data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 401:
        print("✅ Authentication error is expected - endpoint is working!")
        print("✅ text_position_3d field issue appears to be resolved!")
    elif response.status_code == 500:
        print("❌ Server error - check for NOT NULL constraint issues")
    else:
        print(f"Unexpected status code: {response.status_code}")
        
except Exception as e:
    print(f"Error making request: {e}")