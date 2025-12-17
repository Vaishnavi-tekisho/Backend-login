"""
LeadQ Backend - Main Application Entry Point
FastAPI application with Supabase database.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Import routers from new structure
from app.routers.auth_router import router as auth_router
from app.routers.password_router import router as password_router
from app.routers.otp_router import router as otp_router
from app.routers.user_router import router as user_router

# Initialize FastAPI application
app = FastAPI(
    title="LeadQ API",
    description="Authentication and User Management API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)       # /auth/* endpoints
app.include_router(password_router)   # /auth/forgot-password, /auth/reset-password
app.include_router(otp_router)        # /auth/send-otp, /auth/verify-otp
app.include_router(user_router)       # /users/* endpoints


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {"status": "ok", "message": "LeadQ API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    print("🚀 LeadQ API Starting...")
    print("📋 Available Routes:")
    for route in app.routes:
        if hasattr(route, 'methods'):
            print(f"  {route.methods} {route.path}")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    print(f"DEBUG: Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    print(f"DEBUG: HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

    
