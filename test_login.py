import requests
import json

def test_login():
    url = "http://localhost:8000/auth/login"
    payload = {
        "email": "ginnavaishnavi1214@gmail.com",
        "password": "password123",  # Assuming this is the password, or testing for "Incorrect password" instead of "User not found"
        "remember_me": False
    }
    
    print(f"Attempting login for: {payload['email']}")
    try:
        response = requests.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("Login SUCCESS!")
        elif response.status_code == 401:
            print("Login Failed (Expected if password wrong, but User Found)")
            # If detail is "Incorrect email or password", it means user was found but password failed, 
            # OR user wasn't found (if we handle it that way).
            # But previously, if user wasn't found via RLS, it might have been returning something else or failing silently?
            # Actually RLS usually returns empty data, so `user` is None.
            # Code: if not user ... raise Incorrect email or password.
            pass
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
