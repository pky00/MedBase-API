import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.utility.config import settings
from app.utility.database import init_db
from app.utility.logging import setup_logging, RequestLoggingMiddleware
from app.router import (
    auth,
    user,
    medicine_category,
    equipment_category,
    medical_device_category,
    medicine,
    equipment,
    medical_device,
    inventory,
)

logger = logging.getLogger("medbase.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    setup_logging(debug=settings.DEBUG)
    logger.info("MedBase API starting up")
    yield
    # Shutdown
    logger.info("MedBase API shutting down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="MedBase - Clinic Management System API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Request/response logging middleware
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(user.router, prefix=settings.API_V1_PREFIX)
app.include_router(medicine_category.router, prefix=settings.API_V1_PREFIX)
app.include_router(equipment_category.router, prefix=settings.API_V1_PREFIX)
app.include_router(medical_device_category.router, prefix=settings.API_V1_PREFIX)
app.include_router(medicine.router, prefix=settings.API_V1_PREFIX)
app.include_router(equipment.router, prefix=settings.API_V1_PREFIX)
app.include_router(medical_device.router, prefix=settings.API_V1_PREFIX)
app.include_router(inventory.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "message": "Welcome to MedBase API",
        "status": "healthy",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
