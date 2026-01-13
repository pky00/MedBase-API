from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette_context import plugins
from starlette_context.middleware import RawContextMiddleware
from app.config import get_settings
from app.routers import auth_router, users_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API for MedBase Clinic Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Context middleware (must be added before other middleware)
app.add_middleware(
    RawContextMiddleware,
    plugins=(plugins.RequestIdPlugin(), plugins.CorrelationIdPlugin()),
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "message": "Welcome to MedBase API",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "debug": settings.debug
    }

