from sqlalchemy import Column, String, Boolean

from app.model.base import BaseModel


class ThirdParty(BaseModel):
    """Base identity table for all persons/entities (users, doctors, patients, partners).

    Created automatically when any linked entity is created.
    """

    __tablename__ = "third_parties"

    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # user, doctor, patient, partner
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
