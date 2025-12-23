# Quick Reference - Auth Module Migration

## 📍 Location Map

### Before (app/ structure)
```
app/
├── routers/
│   ├── auth_router.py      (signup, login, google oauth)
│   ├── password_router.py  (forgot-password, reset-password)
│   ├── otp_router.py       (send-otp, verify-otp)
│   └── user_router.py      (/users/me, /users/{id})
├── services/
│   ├── password_reset_service.py
│   ├── otp_service.py
│   ├── user_service.py
│   ├── verification_service.py
│   └── email_service.py
├── models/
│   ├── user_model.py
│   └── otp_model.py
├── middleware/
│   └── auth_middleware.py
├── utils/
│   ├── password_utils.py
│   ├── token_utils.py
│   └── common.py
└── core/
    ├── config.py
    ├── security.py
    └── database.py
```

### After (src/ structure)
```
src/
├── core/                    # Shared app-wide utilities
│   ├── config.py           # (moved from app/core/)
│   ├── security.py         # (moved from app/core/)
│   ├── database.py         # (moved from app/db/)
│   ├── middleware.py       # (moved from app/middleware/)
│   ├── exceptions.py       # (NEW)
│   └── logging.py          # (NEW)
├── modules/auth/           # Auth module - fully consolidated
│   ├── router.py           # ALL endpoints (consolidated from 4 routers)
│   ├── schemas.py          # ALL models (user + otp)
│   ├── service.py          # ALL services (5 service classes)
│   ├── repository.py       # Database layer (NEW)
│   ├── utils.py            # Helpers (password + otp)
│   └── constants.py        # Fixed values (NEW)
└── shared/                 # Cross-module utilities
    ├── responses.py        # Common response models (NEW)
    └── utils.py            # Shared helpers (NEW)
```

---

## 🔗 Import Changes

### Old Way
```python
from app.core.config import settings
from app.core.security import create_access_token
from app.db.supabase_client import get_supabase
from app.middleware.auth_middleware import get_current_user
from app.routers.auth_router import router as auth_router
from app.services.password_reset_service import PasswordResetService
```

### New Way
```python
from src.core.config import settings
from src.core.security import create_access_token
from src.core.database import get_supabase
from src.core.middleware import get_current_user
from src.modules.auth.router import router as auth_router
from src.modules.auth.service import PasswordResetService
```

---

## 📊 Service Classes Reference

### **AuthService**
```python
AuthService.register_user(email, password, first_name, ...)
AuthService.login_user(email, password, remember_me, ...)
```

### **PasswordResetService**
```python
PasswordResetService.request_password_reset(email)
PasswordResetService.verify_reset_otp(email, otp)
PasswordResetService.reset_password(email, otp, new_password)
PasswordResetService.request_password_reset_link(email, redirect_url)
```

### **VerificationService**
```python
VerificationService.request_verification_email(email, redirect_url)
VerificationService.verify_email(email, token)
```

### **OTPService**
```python
OTPService.send_otp(phone_number)
OTPService.verify_otp(phone_number, otp_code)
```

### **EmailService**
```python
EmailService.send_password_reset_otp(to_email, otp)
EmailService.send_password_reset_link(to_email, link, user_context)
EmailService.send_verification_email(to_email, link, user_context)
```

---

## 🗄️ Repository Classes Reference

### **UserRepository**
```python
UserRepository.get_by_email(email)
UserRepository.get_by_id(user_id)
UserRepository.exists(email)
UserRepository.create(user_data)
UserRepository.update(user_id, update_data)
UserRepository.update_by_email(email, update_data)
UserRepository.update_password(email, new_password)
```

### **UserProfileRepository**
```python
UserProfileRepository.get_by_user_id(user_id)
UserProfileRepository.create(profile_data)
UserProfileRepository.update(user_id, update_data)
UserProfileRepository.upsert(user_id, profile_data)
```

### **PasswordResetRepository**
```python
PasswordResetRepository.store_reset_otp(email, hashed_otp, expiry)
PasswordResetRepository.get_reset_otp(email)
PasswordResetRepository.invalidate_reset_otp(email)
```

### **EmailVerificationRepository**
```python
EmailVerificationRepository.store_verification_token(email, hashed_token, expiry)
EmailVerificationRepository.get_verification_token(email)
EmailVerificationRepository.mark_email_verified(email)
```

### **OTPRepository**
```python
OTPRepository.update_phone_verification(phone_number)
```

---

## 🔐 Middleware Reference

### **get_current_user**
```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    supabase = Depends(get_supabase)
) -> dict
```
Validates JWT token and returns user from database.

### **get_current_active_user**
```python
async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict
```
Ensures user is active (is_active=True).

### **get_current_user_optional**
```python
async def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    supabase = Depends(get_supabase)
) -> dict | None
```
Returns None instead of raising if not authenticated.

---

## 🔌 Endpoint Reference

### Authentication (7)
| Endpoint | Method | Auth Required |
|----------|--------|--------------|
| `/auth/signup` | POST | ❌ |
| `/auth/login` | POST | ❌ |
| `/auth/login/token` | POST | ❌ |
| `/auth/google` | GET | ❌ |
| `/auth/callback` | GET | ❌ |
| `/auth/google` | POST | ❌ |
| `/auth/me` | GET | ✅ |

### User Management (3)
| Endpoint | Method | Auth Required |
|----------|--------|--------------|
| `/users/me` | GET | ✅ |
| `/users/me` | PUT | ✅ |
| `/users/{user_id}` | GET | ✅ |

### Password Reset (4)
| Endpoint | Method | Auth Required |
|----------|--------|--------------|
| `/auth/forgot-password` | POST | ❌ |
| `/auth/verify-reset-otp` | POST | ❌ |
| `/auth/reset-password` | POST | ❌ |
| `/auth/request-password-reset-link` | POST | ❌ |

### Email Verification (2)
| Endpoint | Method | Auth Required |
|----------|--------|--------------|
| `/auth/request-verification` | POST | ❌ |
| `/auth/verify-email` | POST | ❌ |

### Phone OTP (2)
| Endpoint | Method | Auth Required |
|----------|--------|--------------|
| `/auth/send-otp` | POST | ❌ |
| `/auth/verify-otp` | POST | ❌ |

---

## 📦 Constants Reference

Located in `src/modules/auth/constants.py`:
```python
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
PASSWORD_RESET_TOKEN_EXPIRY_MINUTES = 15
EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS = 24
TWILIO_SMS_CHANNEL = "sms"
TWILIO_VERIFICATION_APPROVED = "approved"
OAUTH_PROVIDER_EMAIL = "email"
OAUTH_PROVIDER_GOOGLE = "google"
TABLE_USERS_LOGIN = "users_login"
TABLE_USERS_PROFILE = "users_profile_login"
TABLE_USER_OTPS = "user_otps"
```

---

## 🎯 Next Steps

1. **Test the API** - Run the app and test all endpoints
2. **Update Tests** - Update test imports to use new paths
3. **Documentation** - Update API docs to reflect new structure
4. **Other Modules** - Use auth module as template for other modules
5. **Old Code** - Eventually remove old `app/routers/`, `app/services/`, etc.

---

## ✅ Verification Checklist

- [x] All files have correct syntax
- [x] All imports are resolvable
- [x] app/main.py imports from src/modules/auth
- [x] Service classes are properly consolidated
- [x] Repository layer is separate from services
- [x] Schemas include all models
- [x] Constants are centralized
- [x] Middleware is in core
- [x] Exceptions are custom classes
- [x] Documentation is comprehensive
