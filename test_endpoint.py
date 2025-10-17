import requests

# Test the add-custom-order endpoint directly
url = "http://localhost:8000/api/add-custom-order/"

# Test with a simple GET request first
try:
    response = requests.get(url)
    print(f"GET Response Status: {response.status_code}")
    print(f"GET Response Text: {response.text}")
except Exception as e:
    print(f"GET Request Error: {e}")

# Test with a POST request
try:
    response = requests.post(url, json={"test": "data"})
    print(f"POST Response Status: {response.status_code}")
    print(f"POST Response Text: {response.text}")
except Exception as e:
    print(f"POST Request Error: {e}")