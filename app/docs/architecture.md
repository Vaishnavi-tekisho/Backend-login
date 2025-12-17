# LeadQ Backend Architecture

## Overview

LeadQ Backend is a FastAPI-based authentication and user management system using Supabase as the database.

## Folder Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── core/                      # Core settings & app-level configs
│   │   ├── config.py              # Environment variables and secrets
│   │   ├── security.py            # JWT and password hashing utilities
│   │   └── logging_config.py      # Logging configuration
│   │
│   ├── models/                    # Pydantic models (request/response)
│   │   ├── user_model.py          # User-related models
│   │   └── otp_model.py           # OTP-related models
│   │
│   ├── schemas/                   # Database schemas (Supabase tables)
│   │   ├── user_schema.py         # Users table schema
│   │   └── otp_schema.py          # OTP table schema
│   │
│   ├── routers/                   # API endpoints grouped by feature
│   │   ├── auth_router.py         # Authentication endpoints
│   │   ├── password_router.py     # Password reset endpoints
│   │   ├── otp_router.py          # SMS OTP endpoints
│   │   └── user_router.py         # User profile endpoints
│   │
│   ├── services/                  # Business logic layer
│   │   ├── user_service.py        # User operations
│   │   ├── password_reset_service.py  # Password reset logic
│   │   ├── email_service.py       # Email sending via SendGrid
│   │   └── otp_service.py         # SMS OTP via Twilio
│   │
│   ├── db/                        # Supabase DB connection wrapper
│   │   ├── supabase_client.py     # Supabase client initialization
│   │   └── queries/               # SQL query references
│   │       └── user_queries.sql
│   │
│   ├── utils/                     # Helper functions
│   │   ├── token_utils.py         # JWT token utilities
│   │   ├── password_utils.py      # Password validation/hashing
│   │   └── common.py              # Common utilities
│   │
│   ├── middleware/                # Request processing middleware
│   │   └── auth_middleware.py     # JWT authentication middleware
│   │
│   ├── tests/                     # Unit & integration tests
│   │   ├── test_auth.py
│   │   ├── test_user.py
│   │   └── test_password_reset.py
│   │
│   └── docs/                      # Documentation
│       ├── architecture.md
│       ├── api_reference.md
│       └── flows.md
│
├── requirements.txt
├── README.md
├── .env
└── .env.example
```

## Technology Stack

- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt (passlib)
- **Email Service**: SendGrid
- **SMS Service**: Twilio Verify
- **Validation**: Pydantic

## Key Components

### Core Module (`core/`)
- **config.py**: Loads environment variables using Pydantic BaseSettings
- **security.py**: JWT token creation/verification, password hashing
- **logging_config.py**: Centralized logging configuration

### Models Module (`models/`)
Pydantic models for API request/response validation:
- User registration, login, profile models
- OTP request/response models
- Token models

### Schemas Module (`schemas/`)
Database table schema definitions (for documentation/reference):
- Users table structure
- OTP table structure

### Routers Module (`routers/`)
API endpoint handlers:
- **auth_router.py**: Signup, login, Google OAuth
- **password_router.py**: Forgot password, OTP verification, password reset
- **otp_router.py**: SMS OTP send/verify
- **user_router.py**: User profile CRUD

### Services Module (`services/`)
Business logic layer:
- **user_service.py**: User CRUD operations
- **password_reset_service.py**: OTP generation, verification, password update
- **email_service.py**: SendGrid email sending
- **otp_service.py**: Twilio SMS OTP

### Database Module (`db/`)
- **supabase_client.py**: Supabase client initialization and dependency injection

### Middleware Module (`middleware/`)
- **auth_middleware.py**: JWT token validation, current user extraction

## Authentication Flow

### Email/Password Registration
1. User submits email, password, name
2. Backend validates input
3. Password is hashed with bcrypt
4. User record created in Supabase
5. JWT token generated and returned

### Email/Password Login
1. User submits email, password
2. Backend fetches user by email
3. Password verified against hash
4. Last login timestamp updated
5. JWT token generated and returned

### Google OAuth
1. User redirected to Google consent screen
2. Google returns authorization code
3. Backend exchanges code for tokens
4. ID token verified with Google
5. User created/updated in database
6. JWT token generated and returned

## Password Reset Flow

1. **Request Reset**: User submits email → OTP generated → hashed and stored → sent via email
2. **Verify OTP**: User submits OTP → verified against hash → confirmed
3. **Reset Password**: User submits OTP + new password → OTP re-verified → password updated → OTP invalidated

## Environment Variables

```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_public_key
SUPABASE_SECRET_KEY=your_service_role_key

# JWT
SECRET_KEY=your_jwt_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# SendGrid
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=your_verified_email
SENDGRID_DEV_MODE=true

# Twilio
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_VERIFY_SERVICE_SID=your_verify_service_sid
```

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest app/tests/
```
