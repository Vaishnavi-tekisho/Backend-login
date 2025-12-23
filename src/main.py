"""
LeadQ Backend - Main Application Entry Point
FastAPI application with Supabase database.
"""
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

# Import routers from new modular structure
from src.modules.auth.router import router as auth_router

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
app.include_router(auth_router)  # /auth/*, /users/* endpoints


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
    from src.core.config import settings
    if settings.SUPABASE_SECRET_KEY:
        print("✅ Service Role Key LOADED (Admin operations enabled).")
    else:
        print("⚠️ Service Role Key NOT FOUND in settings. Admin operations will fail.")
    print("📋 Available Routes:")
    for route in app.routes:
        if hasattr(route, 'methods'):
            print(f"  {route.methods} {route.path}")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    print(f"DEBUG: Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors()}),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    print(f"DEBUG: HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({"detail": exc.detail}),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    print(f"ERROR: Unhandled Exception: {str(exc)}")
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder({"detail": "Internal Server Error", "error": str(exc)}),
    )

    
