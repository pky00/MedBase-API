from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.doctors import router as doctors_router
from app.routers.patients import router as patients_router
from app.routers.patient_allergies import router as patient_allergies_router
from app.routers.patient_medical_history import router as patient_medical_history_router
from app.routers.donors import router as donors_router
from app.routers.medicine_categories import router as medicine_categories_router
from app.routers.equipment_categories import router as equipment_categories_router
from app.routers.medical_device_categories import router as medical_device_categories_router
from app.routers.medicines import router as medicines_router
from app.routers.equipment import router as equipment_router
from app.routers.medical_devices import router as medical_devices_router
from app.routers.appointments import router as appointments_router
from app.routers.vital_signs import router as vital_signs_router
from app.routers.medical_records import router as medical_records_router
from app.routers.donations import router as donations_router
from app.routers.prescriptions import router as prescriptions_router
from app.routers.prescription_items import router as prescription_items_router
from app.routers.patient_documents import router as patient_documents_router
from app.routers.system_settings import router as system_settings_router
from app.routers.prescribed_devices import router as prescribed_devices_router
from app.routers.inventory_transactions import router as inventory_transactions_router

__all__ = [
    "auth_router",
    "users_router",
    "doctors_router",
    "patients_router",
    "patient_allergies_router",
    "patient_medical_history_router",
    "donors_router",
    "medicine_categories_router",
    "equipment_categories_router",
    "medical_device_categories_router",
    "medicines_router",
    "equipment_router",
    "medical_devices_router",
    "appointments_router",
    "vital_signs_router",
    "medical_records_router",
    "donations_router",
    "prescriptions_router",
    "prescription_items_router",
    "patient_documents_router",
    "system_settings_router",
    "prescribed_devices_router",
    "inventory_transactions_router",
]
