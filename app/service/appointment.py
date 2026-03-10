import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import aliased

from app.model.appointment import Appointment, generate_code
from app.model.vital_sign import VitalSign
from app.model.medical_record import MedicalRecord
from app.model.patient import Patient
from app.model.doctor import Doctor
from app.model.partner import Partner
from app.model.third_party import ThirdParty
from app.schema.appointment import AppointmentCreate, AppointmentUpdate, AppointmentDetailResponse, AppointmentResponse

logger = logging.getLogger("medbase.service.appointment")


class AppointmentService:
    """Service layer for appointment operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, appointment_id: int) -> Optional[Appointment]:
        """Get appointment by ID."""
        result = await self.db.execute(
            select(Appointment).where(
                Appointment.id == appointment_id,
                Appointment.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_details(self, appointment_id: int) -> Optional[AppointmentDetailResponse]:
        """Get appointment by ID with patient/doctor/partner names, vitals, and medical record."""
        PatientTP = aliased(ThirdParty)
        DoctorTP = aliased(ThirdParty)
        PartnerTP = aliased(ThirdParty)
        result = await self.db.execute(
            select(
                Appointment,
                PatientTP.name.label("patient_name"),
                DoctorTP.name.label("doctor_name"),
                PartnerTP.name.label("partner_name"),
                VitalSign,
                MedicalRecord,
            )
            .outerjoin(Patient, Appointment.patient_id == Patient.id)
            .outerjoin(PatientTP, Patient.third_party_id == PatientTP.id)
            .outerjoin(Doctor, Appointment.doctor_id == Doctor.id)
            .outerjoin(DoctorTP, Doctor.third_party_id == DoctorTP.id)
            .outerjoin(Partner, Appointment.partner_id == Partner.id)
            .outerjoin(PartnerTP, Partner.third_party_id == PartnerTP.id)
            .outerjoin(VitalSign, (VitalSign.appointment_id == Appointment.id) & (VitalSign.is_deleted == False))
            .outerjoin(MedicalRecord, (MedicalRecord.appointment_id == Appointment.id) & (MedicalRecord.is_deleted == False))
            .where(
                Appointment.id == appointment_id,
                Appointment.is_deleted == False,
            )
        )
        row = result.one_or_none()
        if not row:
            return None

        return AppointmentDetailResponse.from_row(row, vital_signs=row[4], medical_record=row[5])

    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        patient_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        partner_id: Optional[int] = None,
        status: Optional[str] = None,
        type: Optional[str] = None,
        location: Optional[str] = None,
        appointment_date: Optional[str] = None,
        search: Optional[str] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[dict], int]:
        """Get all appointments with pagination, filtering, and sorting."""
        PatientTP = aliased(ThirdParty)
        DoctorTP = aliased(ThirdParty)
        PartnerTP = aliased(ThirdParty)
        query = (
            select(
                Appointment,
                PatientTP.name.label("patient_name"),
                DoctorTP.name.label("doctor_name"),
                PartnerTP.name.label("partner_name"),
                VitalSign.id.label("vital_sign_id"),
                MedicalRecord.id.label("medical_record_id"),
            )
            .outerjoin(Patient, Appointment.patient_id == Patient.id)
            .outerjoin(PatientTP, Patient.third_party_id == PatientTP.id)
            .outerjoin(Doctor, Appointment.doctor_id == Doctor.id)
            .outerjoin(DoctorTP, Doctor.third_party_id == DoctorTP.id)
            .outerjoin(Partner, Appointment.partner_id == Partner.id)
            .outerjoin(PartnerTP, Partner.third_party_id == PartnerTP.id)
            .outerjoin(VitalSign, (VitalSign.appointment_id == Appointment.id) & (VitalSign.is_deleted == False))
            .outerjoin(MedicalRecord, (MedicalRecord.appointment_id == Appointment.id) & (MedicalRecord.is_deleted == False))
            .where(Appointment.is_deleted == False)
        )

        if patient_id is not None:
            query = query.where(Appointment.patient_id == patient_id)
        if doctor_id is not None:
            query = query.where(Appointment.doctor_id == doctor_id)
        if partner_id is not None:
            query = query.where(Appointment.partner_id == partner_id)
        if status is not None:
            query = query.where(Appointment.status == status)
        if type is not None:
            query = query.where(Appointment.type == type)
        if location is not None:
            query = query.where(Appointment.location == location)
        if appointment_date is not None:
            query = query.where(func.date(Appointment.appointment_date) == appointment_date)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Appointment.code.ilike(search_term),
                    PatientTP.name.ilike(search_term),
                    DoctorTP.name.ilike(search_term),
                    PartnerTP.name.ilike(search_term),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        sort_column = getattr(Appointment, sort, Appointment.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        rows = result.all()

        appointments = [
            AppointmentResponse.from_row(row).model_dump()
            for row in rows
        ]

        logger.debug("Queried appointments: total=%d returned=%d", total, len(appointments))
        return appointments, total

    async def create(self, data: AppointmentCreate, created_by: Optional[str] = None) -> Appointment:
        """Create a new appointment."""
        appointment = Appointment(
            code=generate_code(),
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            partner_id=data.partner_id,
            appointment_date=data.appointment_date,
            status=data.status,
            type=data.type,
            location=data.location,
            notes=data.notes,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(appointment)
        await self.db.flush()
        await self.db.refresh(appointment)

        logger.info("Created appointment id=%d patient_id=%d", appointment.id, data.patient_id)
        return appointment

    async def update(self, appointment_id: int, data: AppointmentUpdate, updated_by: Optional[str] = None) -> Optional[Appointment]:
        """Update an appointment."""
        appointment = await self.get_by_id(appointment_id)
        if not appointment:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(appointment, field, value)

        appointment.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(appointment)

        logger.info("Updated appointment id=%d fields=%s", appointment_id, list(update_data.keys()))
        return appointment

    async def update_status(self, appointment_id: int, status: str, updated_by: Optional[str] = None) -> Optional[Appointment]:
        """Update appointment status."""
        appointment = await self.get_by_id(appointment_id)
        if not appointment:
            return None

        appointment.status = status
        appointment.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(appointment)

        logger.info("Updated appointment id=%d status=%s", appointment_id, status)
        return appointment

    async def delete(self, appointment_id: int, deleted_by: Optional[str] = None) -> bool:
        """Soft delete an appointment."""
        appointment = await self.get_by_id(appointment_id)
        if not appointment:
            return False
        appointment.is_deleted = True
        appointment.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted appointment id=%d", appointment_id)
        return True
