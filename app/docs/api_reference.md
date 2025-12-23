# LeadQ API Reference

## Base URL
```
http://localhost:8000
```

## Authentication Endpoints

### POST /auth/signup
Register a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "user_name": "John Doe",
  "phone_number": "+1234567890",
  "location": "New York"
}
```

**Response:**
```json
{
  "access_token": "<TOKEN>",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "user_name": "John Doe",
    "is_active": true
  }
}
```

### POST /auth/login
Login with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "access_token": "<TOKEN>",
  "token_type": "bearer",
  "user": { ... }
}
```

### GET /auth/google
Redirect to Google OAuth consent screen.

### GET /auth/callback
Handle Google OAuth callback (internal).

### POST /auth/google
Verify Google ID token and authenticate.

**Request Body:**
```json
{
  "token": "google_id_token"
}
```

### GET /auth/me
Get current authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "user_name": "John Doe",
  "is_active": true,
  "email_verified": true
}
```

---

## Password Reset Endpoints

### POST /auth/forgot-password
Request password reset OTP.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP has been sent to your email."
}
```

### POST /auth/verify-reset-otp
Verify password reset OTP.

**Request Body:**
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP verified successfully."
}
```

### POST /auth/reset-password
Reset password with OTP.

**Request Body:**
```json
{
  "email": "user@example.com",
  "otp": "123456",
  "new_password": "NewSecurePassword123!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Password reset successfully."
}
```

---

## OTP Endpoints (SMS)

### POST /auth/send-otp
Send OTP to phone number via SMS.

**Request Body:**
```json
{
  "phone_number": "+1234567890"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP sent successfully"
}
```

### POST /auth/verify-otp
Verify SMS OTP.

**Request Body:**
```json
{
  "phone_number": "+1234567890",
  "otp_code": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP Verified"
}
```

---

## User Endpoints

### GET /users/me
Get current user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

### PUT /users/me
Update current user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "user_name": "New Name",
  "phone_number": "+1987654321",
  "location": "Los Angeles"
}
```

### GET /users/{user_id}
Get user by ID.

**Headers:**
```
Authorization: Bearer <access_token>
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Email already registered"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Account not found. Please create an account first."
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal Error: <error message>"
}
```
