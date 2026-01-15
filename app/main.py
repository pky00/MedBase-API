from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette_context import plugins
from starlette_context.middleware import RawContextMiddleware
from app.config import get_settings
from app.routers import (
    auth_router,
    users_router,
    doctors_router,
    patients_router,
    patient_allergies_router,
    patient_medical_history_router,
    donors_router,
    medicine_categories_router,
    equipment_categories_router,
    medical_device_categories_router,
    medicines_router,
    equipment_router,
    medical_devices_router,
    appointments_router,
    vital_signs_router,
    medical_records_router,
    donations_router,
    prescriptions_router,
    prescription_items_router,
    patient_documents_router,
    system_settings_router,
    prescribed_devices_router,
)

settings = get_settings()

# OpenAPI Tags Metadata
tags_metadata = [
    {
        "name": "Health",
        "description": "Health check endpoints for monitoring API status.",
    },
    {
        "name": "Authentication",
        "description": "Login and JWT token management.",
    },
    {
        "name": "Users",
        "description": "User management - create, read, update, delete system users.",
    },
    {
        "name": "Doctors",
        "description": "Doctor/physician management including credentials and specializations.",
    },
    {
        "name": "Patients",
        "description": "Patient registration and demographic information management.",
    },
    {
        "name": "Patient Allergies",
        "description": "Track patient allergies and reactions.",
    },
    {
        "name": "Patient Medical History",
        "description": "Patient medical history and conditions.",
    },
    {
        "name": "Appointments",
        "description": "Schedule and manage patient appointments with doctors.",
    },
    {
        "name": "Medical Records",
        "description": "Patient visit records, diagnoses, and treatment plans.",
    },
    {
        "name": "Vital Signs",
        "description": "Patient vital signs measurements.",
    },
    {
        "name": "Prescriptions",
        "description": "Manage prescriptions issued to patients.",
    },
    {
        "name": "Prescription Items",
        "description": "Individual medicine items within prescriptions.",
    },
    {
        "name": "Prescribed Devices",
        "description": "Medical devices prescribed to patients (wheelchairs, walkers, etc.).",
    },
    {
        "name": "Donors",
        "description": "Manage donors who contribute medicines, equipment, and devices.",
    },
    {
        "name": "Donations",
        "description": "Track donations received from donors.",
    },
    {
        "name": "Medicines",
        "description": "Medicine catalog and inventory management.",
    },
    {
        "name": "Medicine Categories",
        "description": "Categories for organizing medicines.",
    },
    {
        "name": "Equipment",
        "description": "Clinic equipment inventory (monitors, surgical tools, etc.).",
    },
    {
        "name": "Equipment Categories",
        "description": "Categories for organizing equipment.",
    },
    {
        "name": "Medical Devices",
        "description": "Prescribable medical devices (wheelchairs, walkers, braces).",
    },
    {
        "name": "Medical Device Categories",
        "description": "Categories for organizing medical devices.",
    },
    {
        "name": "Patient Documents",
        "description": "Manage patient documents including external lab results.",
    },
    {
        "name": "System Settings",
        "description": "System configuration and settings.",
    },
]

app = FastAPI(
    title=settings.app_name,
    description="""
## MedBase Clinic Management API

A comprehensive API for managing a **free clinic** that relies on donations.

### Key Features

* **Patient Management** - Registration, allergies, medical history
* **Appointments** - Schedule and track patient visits
* **Prescriptions** - Medicine and medical device prescriptions
* **Inventory** - Medicines, equipment, and medical devices
* **Donations** - Track donations from individuals and organizations
* **Documents** - Store patient documents and lab results

### Authentication

All endpoints (except `/health` and login) require JWT authentication.

1. Call `POST /api/v1/auth/login` with username/password
2. Use the returned `access_token` in the `Authorization: Bearer <token>` header

### Default Credentials

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin` |

⚠️ **Change the default password immediately in production!**
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    contact={
        "name": "MedBase Support",
        "email": "support@medbase.example",
    },
    license_info={
        "name": "Private",
    },
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
app.include_router(doctors_router, prefix="/api/v1")
app.include_router(patients_router, prefix="/api/v1")
app.include_router(patient_allergies_router, prefix="/api/v1")
app.include_router(patient_medical_history_router, prefix="/api/v1")
app.include_router(donors_router, prefix="/api/v1")
app.include_router(medicine_categories_router, prefix="/api/v1")
app.include_router(equipment_categories_router, prefix="/api/v1")
app.include_router(medical_device_categories_router, prefix="/api/v1")
app.include_router(medicines_router, prefix="/api/v1")
app.include_router(equipment_router, prefix="/api/v1")
app.include_router(medical_devices_router, prefix="/api/v1")
app.include_router(appointments_router, prefix="/api/v1")
app.include_router(vital_signs_router, prefix="/api/v1")
app.include_router(medical_records_router, prefix="/api/v1")
app.include_router(donations_router, prefix="/api/v1")
app.include_router(prescriptions_router, prefix="/api/v1")
app.include_router(prescription_items_router, prefix="/api/v1")
app.include_router(patient_documents_router, prefix="/api/v1")
app.include_router(system_settings_router, prefix="/api/v1")
app.include_router(prescribed_devices_router, prefix="/api/v1")


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
