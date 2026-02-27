"""Populate database with dummy data from dummy_data.json."""
import asyncio
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.utility.database import AsyncSessionLocal

from app.service.user import UserService
from app.service.medicine_category import MedicineCategoryService
from app.service.equipment_category import EquipmentCategoryService
from app.service.medical_device_category import MedicalDeviceCategoryService
from app.service.medicine import MedicineService
from app.service.equipment import EquipmentService
from app.service.medical_device import MedicalDeviceService
from app.service.partner import PartnerService
from app.service.doctor import DoctorService
from app.service.patient import PatientService

from app.schema.user import UserCreate
from app.schema.medicine_category import MedicineCategoryCreate
from app.schema.equipment_category import EquipmentCategoryCreate
from app.schema.medical_device_category import MedicalDeviceCategoryCreate
from app.schema.medicine import MedicineCreate
from app.schema.equipment import EquipmentCreate
from app.schema.medical_device import MedicalDeviceCreate
from app.schema.partner import PartnerCreate
from app.schema.doctor import DoctorCreate
from app.schema.patient import PatientCreate

CREATED_BY = "admin"


def load_data() -> dict:
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dummy_data.json")
    with open(data_path, "r") as f:
        return json.load(f)


async def populate():
    data = load_data()

    async with AsyncSessionLocal() as db:
        # --- Users ---
        user_service = UserService(db)
        for u in data.get("users", []):
            existing = await user_service.get_by_username(u["username"])
            if existing:
                print(f"  [skip] User '{u['username']}' already exists")
                continue
            await user_service.create(
                UserCreate(**u),
                created_by=CREATED_BY,
            )
            print(f"  [created] User '{u['username']}'")

        await db.commit()

        # --- Medicine Categories ---
        med_cat_service = MedicineCategoryService(db)
        med_cat_map = {}
        for c in data.get("medicine_categories", []):
            existing = await med_cat_service.get_by_name(c["name"])
            if existing:
                med_cat_map[c["name"]] = existing.id
                print(f"  [skip] Medicine category '{c['name']}' already exists")
                continue
            cat = await med_cat_service.create(
                MedicineCategoryCreate(**c),
                created_by=CREATED_BY,
            )
            med_cat_map[c["name"]] = cat.id
            print(f"  [created] Medicine category '{c['name']}'")

        await db.commit()

        # --- Equipment Categories ---
        equip_cat_service = EquipmentCategoryService(db)
        equip_cat_map = {}
        for c in data.get("equipment_categories", []):
            existing = await equip_cat_service.get_by_name(c["name"])
            if existing:
                equip_cat_map[c["name"]] = existing.id
                print(f"  [skip] Equipment category '{c['name']}' already exists")
                continue
            cat = await equip_cat_service.create(
                EquipmentCategoryCreate(**c),
                created_by=CREATED_BY,
            )
            equip_cat_map[c["name"]] = cat.id
            print(f"  [created] Equipment category '{c['name']}'")

        await db.commit()

        # --- Medical Device Categories ---
        dev_cat_service = MedicalDeviceCategoryService(db)
        dev_cat_map = {}
        for c in data.get("medical_device_categories", []):
            existing = await dev_cat_service.get_by_name(c["name"])
            if existing:
                dev_cat_map[c["name"]] = existing.id
                print(f"  [skip] Medical device category '{c['name']}' already exists")
                continue
            cat = await dev_cat_service.create(
                MedicalDeviceCategoryCreate(**c),
                created_by=CREATED_BY,
            )
            dev_cat_map[c["name"]] = cat.id
            print(f"  [created] Medical device category '{c['name']}'")

        await db.commit()

        # --- Medicines ---
        med_service = MedicineService(db)
        for m in data.get("medicines", []):
            existing = await med_service.get_by_name(m["name"])
            if existing:
                print(f"  [skip] Medicine '{m['name']}' already exists")
                continue
            category_id = med_cat_map.get(m.pop("category", None))
            await med_service.create(
                MedicineCreate(category_id=category_id, **m),
                created_by=CREATED_BY,
            )
            print(f"  [created] Medicine '{m['name']}'")

        await db.commit()

        # --- Equipment ---
        equip_service = EquipmentService(db)
        for e in data.get("equipment", []):
            existing = await equip_service.get_by_name(e["name"])
            if existing:
                print(f"  [skip] Equipment '{e['name']}' already exists")
                continue
            category_id = equip_cat_map.get(e.pop("category", None))
            await equip_service.create(
                EquipmentCreate(category_id=category_id, **e),
                created_by=CREATED_BY,
            )
            print(f"  [created] Equipment '{e['name']}'")

        await db.commit()

        # --- Medical Devices ---
        dev_service = MedicalDeviceService(db)
        for d in data.get("medical_devices", []):
            existing = await dev_service.get_by_name(d["name"])
            if existing:
                print(f"  [skip] Medical device '{d['name']}' already exists")
                continue
            category_id = dev_cat_map.get(d.pop("category", None))
            await dev_service.create(
                MedicalDeviceCreate(category_id=category_id, **d),
                created_by=CREATED_BY,
            )
            print(f"  [created] Medical device '{d['name']}'")

        await db.commit()

        # --- Partners ---
        partner_service = PartnerService(db)
        partner_map = {}
        for p in data.get("partners", []):
            existing = await partner_service.get_by_name(p["name"])
            if existing:
                partner_map[p["name"]] = existing.id
                print(f"  [skip] Partner '{p['name']}' already exists")
                continue
            partner = await partner_service.create(
                PartnerCreate(**p),
                created_by=CREATED_BY,
            )
            partner_map[p["name"]] = partner.id
            print(f"  [created] Partner '{p['name']}'")

        await db.commit()

        # --- Doctors ---
        doctor_service = DoctorService(db)
        for d in data.get("doctors", []):
            existing = await doctor_service.get_by_name(d["name"])
            if existing:
                print(f"  [skip] Doctor '{d['name']}' already exists")
                continue
            partner_name = d.pop("partner_name", None)
            if partner_name:
                d["partner_id"] = partner_map.get(partner_name)
            await doctor_service.create(
                DoctorCreate(**d),
                created_by=CREATED_BY,
            )
            print(f"  [created] Doctor '{d['name']}'")

        await db.commit()

        # --- Patients ---
        patient_service = PatientService(db)
        for p in data.get("patients", []):
            existing = await patient_service.get_by_name(p["first_name"], p["last_name"])
            if existing:
                print(f"  [skip] Patient '{p['first_name']} {p['last_name']}' already exists")
                continue
            await patient_service.create(
                PatientCreate(**p),
                created_by=CREATED_BY,
            )
            print(f"  [created] Patient '{p['first_name']} {p['last_name']}'")

        await db.commit()

    print("\nDummy data population complete!")


if __name__ == "__main__":
    print("Populating dummy data...")
    asyncio.run(populate())
