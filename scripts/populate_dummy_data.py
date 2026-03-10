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
from app.service.appointment import AppointmentService
from app.service.vital_sign import VitalSignService
from app.service.medical_record import MedicalRecordService
from app.service.treatment import TreatmentService
from app.service.inventory_transaction import InventoryTransactionService

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
from app.schema.appointment import AppointmentCreate
from app.schema.vital_sign import VitalSignCreate
from app.schema.medical_record import MedicalRecordCreate
from app.schema.treatment import TreatmentCreate
from app.schema.inventory_transaction import InventoryTransactionCreate, TransactionItemCreate

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
        doctor_map = {}
        for d in data.get("doctors", []):
            existing = await doctor_service.get_by_name(d["name"])
            if existing:
                doctor_map[d["name"]] = existing.id
                print(f"  [skip] Doctor '{d['name']}' already exists")
                continue
            partner_name = d.pop("partner_name", None)
            if partner_name:
                d["partner_id"] = partner_map.get(partner_name)
            doctor = await doctor_service.create(
                DoctorCreate(**d),
                created_by=CREATED_BY,
            )
            doctor_map[d["name"]] = doctor.id
            print(f"  [created] Doctor '{d['name']}'")

        await db.commit()

        # --- Patients ---
        patient_service = PatientService(db)
        patient_map = {}
        for p in data.get("patients", []):
            existing = await patient_service.get_by_name(p["name"])
            if existing:
                patient_map[p["name"]] = existing.id
                print(f"  [skip] Patient '{p['name']}' already exists")
                continue
            patient = await patient_service.create(
                PatientCreate(**p),
                created_by=CREATED_BY,
            )
            patient_map[p["name"]] = patient.id
            print(f"  [created] Patient '{p['name']}'")

        await db.commit()

        # --- Appointments ---
        appt_service = AppointmentService(db)
        appointment_ids = []
        for a in data.get("appointments", []):
            appt_data = {
                "patient_id": patient_map.get(a["patient_name"]),
                "doctor_id": doctor_map.get(a.get("doctor_name")),
                "appointment_date": a["appointment_date"],
                "type": a["type"],
                "location": a.get("location", "internal"),
                "status": a.get("status", "scheduled"),
                "notes": a.get("notes"),
            }
            if a.get("partner_name"):
                appt_data["partner_id"] = partner_map.get(a["partner_name"])
            appt = await appt_service.create(
                AppointmentCreate(**appt_data),
                created_by=CREATED_BY,
            )
            appointment_ids.append(appt.id)
            print(f"  [created] Appointment id={appt.id} for patient '{a['patient_name']}'")

        await db.commit()

        # --- Vital Signs ---
        vital_service = VitalSignService(db)
        for v in data.get("vital_signs", []):
            appt_index = v.pop("appointment_index")
            if appt_index >= len(appointment_ids):
                print(f"  [skip] Vital sign - appointment index {appt_index} out of range")
                continue
            appt_id = appointment_ids[appt_index]
            existing = await vital_service.get_by_appointment_id(appt_id)
            if existing:
                print(f"  [skip] Vital signs for appointment id={appt_id} already exist")
                continue
            vital = await vital_service.create(
                appt_id,
                VitalSignCreate(**v),
                created_by=CREATED_BY,
            )
            print(f"  [created] Vital signs id={vital.id} for appointment id={appt_id}")

        await db.commit()

        # --- Medical Records ---
        record_service = MedicalRecordService(db)
        for mr in data.get("medical_records", []):
            appt_index = mr.pop("appointment_index")
            if appt_index >= len(appointment_ids):
                print(f"  [skip] Medical record - appointment index {appt_index} out of range")
                continue
            appt_id = appointment_ids[appt_index]
            existing = await record_service.get_by_appointment_id(appt_id)
            if existing:
                print(f"  [skip] Medical record for appointment id={appt_id} already exists")
                continue
            record = await record_service.create(
                appt_id,
                MedicalRecordCreate(**mr),
                created_by=CREATED_BY,
            )
            print(f"  [created] Medical record id={record.id} for appointment id={appt_id}")

        await db.commit()

        # --- Treatments ---
        treatment_service = TreatmentService(db)
        for t in data.get("treatments", []):
            treatment_data = {
                "patient_id": patient_map.get(t["patient_name"]),
                "partner_id": partner_map.get(t["partner_name"]),
                "treatment_type": t["treatment_type"],
                "description": t.get("description"),
                "treatment_date": t.get("treatment_date"),
                "cost": t.get("cost"),
                "notes": t.get("notes"),
            }
            if "appointment_index" in t and t["appointment_index"] < len(appointment_ids):
                treatment_data["appointment_id"] = appointment_ids[t["appointment_index"]]
            treatment = await treatment_service.create(
                TreatmentCreate(**treatment_data),
                created_by=CREATED_BY,
            )
            print(f"  [created] Treatment id={treatment.id} '{t['treatment_type']}' for patient '{t['patient_name']}'")

        await db.commit()

        # --- Inventory Transactions ---
        tx_service = InventoryTransactionService(db)

        # Build item name -> id maps for resolving item references
        item_id_map = {}
        for m in data.get("medicines", []):
            med = await med_service.get_by_name(m["name"])
            if med:
                item_id_map[("medicine", m["name"])] = med.id
        for e in data.get("equipment", []):
            eq = await equip_service.get_by_name(e["name"])
            if eq:
                item_id_map[("equipment", e["name"])] = eq.id
        for d in data.get("medical_devices", []):
            dev = await dev_service.get_by_name(d["name"])
            if dev:
                item_id_map[("medical_device", d["name"])] = dev.id

        # Build partner name -> third_party_id map
        partner_tp_map = {}
        for p in data.get("partners", []):
            partner = await partner_service.get_by_name(p["name"])
            if partner:
                partner_tp_map[p["name"]] = partner.third_party_id

        # Build doctor name -> third_party_id map
        doctor_tp_map = {}
        for d in data.get("doctors", []):
            doctor = await doctor_service.get_by_name(d["name"])
            if doctor:
                doctor_tp_map[d["name"]] = doctor.third_party_id

        # Get admin user's third_party_id for auto-set types
        admin = await user_service.get_by_username("admin")
        admin_tp_id = admin.third_party_id if admin else None

        auto_tp_types = {"purchase", "loss", "breakage", "expiration", "destruction"}

        for tx in data.get("inventory_transactions", []):
            tx_type = tx["transaction_type"]

            # Resolve third_party_id
            if tx_type in auto_tp_types:
                third_party_id = admin_tp_id
            elif tx_type == "donation":
                third_party_id = partner_tp_map.get(tx.get("partner_name"))
            elif tx_type == "prescription":
                third_party_id = doctor_tp_map.get(tx.get("doctor_name"))
            else:
                third_party_id = admin_tp_id

            if not third_party_id:
                print(f"  [skip] Transaction '{tx_type}' - could not resolve third_party_id")
                continue

            # Resolve items
            items = []
            for item in tx.get("items", []):
                item_id = item_id_map.get((item["item_type"], item["item_name"]))
                if not item_id:
                    print(f"  [skip] Item '{item['item_name']}' ({item['item_type']}) not found")
                    continue
                items.append(TransactionItemCreate(
                    item_type=item["item_type"],
                    item_id=item_id,
                    quantity=item["quantity"],
                ))

            # Resolve appointment_id if provided
            appt_id = None
            if "appointment_index" in tx and tx["appointment_index"] < len(appointment_ids):
                appt_id = appointment_ids[tx["appointment_index"]]

            tx_data = InventoryTransactionCreate(
                transaction_type=tx_type,
                third_party_id=third_party_id,
                appointment_id=appt_id,
                transaction_date=tx["transaction_date"],
                notes=tx.get("notes"),
                items=items if items else None,
            )
            transaction = await tx_service.create(tx_data, third_party_id, created_by=CREATED_BY)
            item_count = len(items)
            label = tx.get("partner_name") or tx.get("doctor_name") or "admin"
            print(f"  [created] Transaction id={transaction.id} type={tx_type} ({label}) with {item_count} items")

        await db.commit()

    print("\nDummy data population complete!")


if __name__ == "__main__":
    print("Populating dummy data...")
    asyncio.run(populate())
