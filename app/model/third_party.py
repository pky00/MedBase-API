from sqlalchemy import Column, String, Boolean

from app.model.base import BaseModel


class ThirdParty(BaseModel):
    """Base identity table for all persons/entities (users, doctors, patients, partners).

    A third party can be linked to multiple entities simultaneously (e.g., a person
    can be a user, doctor, patient, and partner at the same time). The type is
    determined by the linked entities, not stored on this record.
    """

    __tablename__ = "third_parties"

    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
