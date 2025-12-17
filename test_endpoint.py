import requests
import json

base_url = "http://127.0.0.1:8000"

print("Checking /openapi.json to see registered routes...")
try:
    resp = requests.get(f"{base_url}/openapi.json")
    if resp.status_code == 200:
        schema = resp.json()
        paths = schema.get("paths", {})
        print("Registered Paths:")
        for path, methods in paths.items():
            print(f"  {path} : {list(methods.keys())}")
            
        if "/auth/verify-otp" in paths:
             print("\n/auth/verify-otp FOUND!")
        else:
             print("\n/auth/verify-otp NOT FOUND in openapi.json")
    else:
        print(f"Failed to get openapi.json: {resp.status_code}")
except Exception as e:
    print(f"Error fetching openapi: {e}")

print("\nTesting POST /auth/verify-otp...")
url = f"{base_url}/auth/verify-otp"
payload = {
    "phone_number": "+15550000000",
    "otp_code": "000000"
}
try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
except Exception as e:
    print(f"Error posting: {e}")
