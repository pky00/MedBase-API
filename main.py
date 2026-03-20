import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html

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
    third_party,
    partner,
    doctor,
    patient,
    patient_document,
    appointment,
    vital_sign,
    medical_record,
    treatment,
    inventory_transaction,
    inventory_transaction_item,
    statistics,
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
    redoc_url=None,
    openapi_url="/openapi.json",
    lifespan=lifespan
)


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.5/bundles/redoc.standalone.js",
    )

# Request/response logging middleware
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
if settings.ENV == "LOCAL":
    cors_origins = ["*"]
    cors_credentials = False
else:
    cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
    cors_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(user.router, prefix=settings.API_V1_PREFIX)
app.include_router(third_party.router, prefix=settings.API_V1_PREFIX)
app.include_router(medicine_category.router, prefix=settings.API_V1_PREFIX)
app.include_router(equipment_category.router, prefix=settings.API_V1_PREFIX)
app.include_router(medical_device_category.router, prefix=settings.API_V1_PREFIX)
app.include_router(medicine.router, prefix=settings.API_V1_PREFIX)
app.include_router(equipment.router, prefix=settings.API_V1_PREFIX)
app.include_router(medical_device.router, prefix=settings.API_V1_PREFIX)
app.include_router(inventory.router, prefix=settings.API_V1_PREFIX)
app.include_router(partner.router, prefix=settings.API_V1_PREFIX)
app.include_router(doctor.router, prefix=settings.API_V1_PREFIX)
app.include_router(patient.router, prefix=settings.API_V1_PREFIX)
app.include_router(patient_document.router, prefix=settings.API_V1_PREFIX)
app.include_router(appointment.router, prefix=settings.API_V1_PREFIX)
app.include_router(vital_sign.router, prefix=settings.API_V1_PREFIX)
app.include_router(medical_record.router, prefix=settings.API_V1_PREFIX)
app.include_router(treatment.router, prefix=settings.API_V1_PREFIX)
app.include_router(inventory_transaction.router, prefix=settings.API_V1_PREFIX)
app.include_router(inventory_transaction_item.router, prefix=settings.API_V1_PREFIX)
app.include_router(statistics.router, prefix=settings.API_V1_PREFIX)


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
