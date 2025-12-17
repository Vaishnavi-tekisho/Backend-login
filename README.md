# LeadQ Backend

A FastAPI-based authentication and user management system using Supabase.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
```

### 3. Run the Server
```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Access API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── main.py              # Application entry point
│   ├── core/                # Configuration & security
│   ├── models/              # Pydantic request/response models
│   ├── schemas/             # Database schemas
│   ├── routers/             # API endpoints
│   ├── services/            # Business logic
│   ├── db/                  # Database client
│   ├── utils/               # Helper functions
│   ├── middleware/          # Request middleware
│   ├── tests/               # Unit tests
│   └── docs/                # Documentation
├── requirements.txt
├── .env.example
└── README.md
```

## API Endpoints

### Authentication
- `POST /auth/signup` - Register new user
- `POST /auth/login` - Login with email/password
- `GET /auth/google` - Google OAuth login
- `GET /auth/me` - Get current user

### Password Reset
- `POST /auth/forgot-password` - Request OTP
- `POST /auth/verify-reset-otp` - Verify OTP
- `POST /auth/reset-password` - Reset password

### Users
- `GET /users/me` - Get profile
- `PUT /users/me` - Update profile

## Development

### Run Tests
```bash
pytest app/tests/
```

### Dev Mode for Emails
Set `SENDGRID_DEV_MODE=true` in `.env` to log emails to console instead of sending.

## Documentation

See [app/docs/](app/docs/) for detailed documentation:
- [architecture.md](app/docs/architecture.md) - System architecture
- [api_reference.md](app/docs/api_reference.md) - API documentation
- [flows.md](app/docs/flows.md) - Authentication flows
