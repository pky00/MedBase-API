import logging
from datetime import date
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate

logger = logging.getLogger(__name__)


class AppointmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, appointment_id: UUID) -> Appointment | None:
        result = await self.db.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_number(self, appointment_number: str) -> Appointment | None:
        result = await self.db.execute(
            select(Appointment).where(Appointment.appointment_number == appointment_number)
        )
        return result.scalar_one_or_none()

    async def _generate_appointment_number(self) -> str:
        """Generate next appointment number in format APT-YYYY-NNNNNN"""
        import datetime as dt
        year = dt.datetime.now().year
        prefix = f"APT-{year}-"
        
        result = await self.db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.appointment_number.like(f"{prefix}%")
            )
        )
        count = result.scalar() or 0
        return f"{prefix}{str(count + 1).zfill(6)}"

    async def list_appointments(
        self,
        page: int = 1,
        size: int = 10,
        patient_id: UUID | None = None,
        doctor_id: UUID | None = None,
        status: AppointmentStatus | None = None,
        appointment_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[Appointment], int]:
        logger.info(f"Listing appointments: page={page}, size={size}")
        query = select(Appointment)
        count_query = select(func.count(Appointment.id))

        if patient_id:
            query = query.where(Appointment.patient_id == patient_id)
            count_query = count_query.where(Appointment.patient_id == patient_id)

        if doctor_id:
            query = query.where(Appointment.doctor_id == doctor_id)
            count_query = count_query.where(Appointment.doctor_id == doctor_id)

        if status:
            query = query.where(Appointment.status == status)
            count_query = count_query.where(Appointment.status == status)

        if appointment_date:
            query = query.where(Appointment.appointment_date == appointment_date)
            count_query = count_query.where(Appointment.appointment_date == appointment_date)

        if date_from:
            query = query.where(Appointment.appointment_date >= date_from)
            count_query = count_query.where(Appointment.appointment_date >= date_from)

        if date_to:
            query = query.where(Appointment.appointment_date <= date_to)
            count_query = count_query.where(Appointment.appointment_date <= date_to)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(
            Appointment.appointment_date.desc(), Appointment.start_time.desc()
        )
        result = await self.db.execute(query)
        appointments = list(result.scalars().all())

        return appointments, total

    async def create(self, data: AppointmentCreate, created_by: str) -> Appointment:
        logger.info(f"Creating appointment for patient: {data.patient_id}")
        appointment_number = await self._generate_appointment_number()
        appointment = Appointment(
            **data.model_dump(),
            appointment_number=appointment_number,
            status=AppointmentStatus.scheduled,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(appointment)
        await self.db.commit()
        await self.db.refresh(appointment)
        logger.info(f"Created appointment: {appointment_number}")
        return appointment

    async def update(
        self, appointment: Appointment, data: AppointmentUpdate, updated_by: str
    ) -> Appointment:
        logger.info(f"Updating appointment: {appointment.appointment_number}")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(appointment, field, value)
        appointment.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(appointment)
        return appointment

    async def delete(self, appointment: Appointment) -> None:
        logger.info(f"Deleting appointment: {appointment.appointment_number}")
        await self.db.delete(appointment)
        await self.db.commit()

