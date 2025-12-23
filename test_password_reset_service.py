from app.services.password_reset_service import PasswordResetService

def test_reset_request():
    email = "ginnavaishnavi1214@gmail.com"
    print(f"Testing password reset request for: {email}")
    
    result = PasswordResetService.request_password_reset(email)
    print(f"Result: {result}")

if __name__ == "__main__":
    test_reset_request()
