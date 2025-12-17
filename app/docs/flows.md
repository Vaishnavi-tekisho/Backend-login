# LeadQ Authentication Flows

## 1. Email/Password Registration Flow

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Client    │         │   Backend   │         │  Supabase   │
└─────────────┘         └─────────────┘         └─────────────┘
       │                       │                       │
       │  POST /auth/signup    │                       │
       │──────────────────────>│                       │
       │  {email, password,    │                       │
       │   user_name}          │                       │
       │                       │                       │
       │                       │  Check existing user  │
       │                       │──────────────────────>│
       │                       │                       │
       │                       │  Hash password        │
       │                       │  (bcrypt)             │
       │                       │                       │
       │                       │  Insert user          │
       │                       │──────────────────────>│
       │                       │                       │
       │                       │  Generate JWT         │
       │                       │                       │
       │  {token, user}        │                       │
       │<──────────────────────│                       │
       │                       │                       │
```

## 2. Email/Password Login Flow

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Client    │         │   Backend   │         │  Supabase   │
└─────────────┘         └─────────────┘         └─────────────┘
       │                       │                       │
       │  POST /auth/login     │                       │
       │──────────────────────>│                       │
       │  {email, password}    │                       │
       │                       │                       │
       │                       │  Get user by email    │
       │                       │──────────────────────>│
       │                       │                       │
       │                       │  Verify password      │
       │                       │  (bcrypt compare)     │
       │                       │                       │
       │                       │  Update last_login    │
       │                       │──────────────────────>│
       │                       │                       │
       │                       │  Generate JWT         │
       │                       │                       │
       │  {token, user}        │                       │
       │<──────────────────────│                       │
       │                       │                       │
```

## 3. Google OAuth Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │    │   Backend   │    │   Google    │    │  Supabase   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                 │                  │                  │
       │  Click "Login   │                  │                  │
       │  with Google"   │                  │                  │
       │────────────────>│                  │                  │
       │                 │                  │                  │
       │                 │  Redirect to     │                  │
       │                 │  consent screen  │                  │
       │<────────────────│────────────────->│                  │
       │                 │                  │                  │
       │  User approves  │                  │                  │
       │                 │                  │                  │
       │                 │  Callback with   │                  │
       │                 │  auth code       │                  │
       │                 │<─────────────────│                  │
       │                 │                  │                  │
       │                 │  Exchange code   │                  │
       │                 │  for tokens      │                  │
       │                 │─────────────────>│                  │
       │                 │                  │                  │
       │                 │  Verify ID token │                  │
       │                 │─────────────────>│                  │
       │                 │                  │                  │
       │                 │  Create/Update   │                  │
       │                 │  user            │                  │
       │                 │──────────────────│─────────────────>│
       │                 │                  │                  │
       │                 │  Generate JWT    │                  │
       │                 │                  │                  │
       │  Redirect with  │                  │                  │
       │  token & user   │                  │                  │
       │<────────────────│                  │                  │
       │                 │                  │                  │
```

## 4. Password Reset Flow (OTP-based)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │    │   Backend   │    │  Supabase   │    │  SendGrid   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                 │                  │                  │
       │  STEP 1: Request OTP              │                  │
       │  POST /auth/forgot-password       │                  │
       │────────────────>│                  │                  │
       │  {email}        │                  │                  │
       │                 │                  │                  │
       │                 │  Check user      │                  │
       │                 │  exists          │                  │
       │                 │─────────────────>│                  │
       │                 │                  │                  │
       │                 │  Generate OTP    │                  │
       │                 │  (6 digits)      │                  │
       │                 │                  │                  │
       │                 │  Hash OTP        │                  │
       │                 │  Store in DB     │                  │
       │                 │─────────────────>│                  │
       │                 │                  │                  │
       │                 │  Send OTP email  │                  │
       │                 │──────────────────│─────────────────>│
       │                 │                  │                  │
       │  {success}      │                  │                  │
       │<────────────────│                  │                  │
       │                 │                  │                  │
       │                 │                  │                  │
       │  STEP 2: Verify OTP               │                  │
       │  POST /auth/verify-reset-otp      │                  │
       │────────────────>│                  │                  │
       │  {email, otp}   │                  │                  │
       │                 │                  │                  │
       │                 │  Get stored      │                  │
       │                 │  OTP hash        │                  │
       │                 │─────────────────>│                  │
       │                 │                  │                  │
       │                 │  Check expiry    │                  │
       │                 │  Verify OTP hash │                  │
       │                 │                  │                  │
       │  {success}      │                  │                  │
       │<────────────────│                  │                  │
       │                 │                  │                  │
       │                 │                  │                  │
       │  STEP 3: Reset Password           │                  │
       │  POST /auth/reset-password        │                  │
       │────────────────>│                  │                  │
       │  {email, otp,   │                  │                  │
       │   new_password} │                  │                  │
       │                 │                  │                  │
       │                 │  Re-verify OTP   │                  │
       │                 │─────────────────>│                  │
       │                 │                  │                  │
       │                 │  Hash new        │                  │
       │                 │  password        │                  │
       │                 │                  │                  │
       │                 │  Update password │                  │
       │                 │  Invalidate OTP  │                  │
       │                 │─────────────────>│                  │
       │                 │                  │                  │
       │  {success}      │                  │                  │
       │<────────────────│                  │                  │
       │                 │                  │                  │
```

## 5. Protected Route Access Flow

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Client    │         │  Middleware │         │   Router    │
└─────────────┘         └─────────────┘         └─────────────┘
       │                       │                       │
       │  GET /auth/me         │                       │
       │  Authorization:       │                       │
       │  Bearer <token>       │                       │
       │──────────────────────>│                       │
       │                       │                       │
       │                       │  Extract token        │
       │                       │  Decode JWT           │
       │                       │  Validate signature   │
       │                       │  Check expiry         │
       │                       │                       │
       │                       │  Query user           │
       │                       │  by email             │
       │                       │                       │
       │                       │  Inject user          │
       │                       │  into request         │
       │                       │──────────────────────>│
       │                       │                       │
       │                       │  Process request      │
       │                       │                       │
       │  {user data}          │                       │
       │<──────────────────────│<──────────────────────│
       │                       │                       │
```

## Security Considerations

1. **Password Storage**: Passwords are hashed using bcrypt before storage
2. **OTP Security**: OTPs are also hashed before storage and have 5-minute expiry
3. **JWT Tokens**: Signed with HS256, expire after 30 minutes
4. **Rate Limiting**: Consider implementing rate limiting for auth endpoints
5. **CORS**: Properly configured for allowed origins
6. **HTTPS**: All production traffic should use HTTPS
