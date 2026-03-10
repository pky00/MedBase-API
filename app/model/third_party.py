import secrets

from sqlalchemy import Column, String, Boolean

from app.model.base import BaseModel

# Unambiguous characters: no 0/O, 1/I/L
_CODE_CHARS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def generate_code() -> str:
    """Generate a unique 6-character human-readable code for third parties."""
    return "".join(secrets.choice(_CODE_CHARS) for _ in range(6))


class ThirdParty(BaseModel):
    """Base identity table for all persons/entities (users, doctors, patients, partners).

    A third party can be linked to multiple entities simultaneously (e.g., a person
    can be a user, doctor, patient, and partner at the same time). The type is
    determined by the linked entities, not stored on this record.
    """

    __tablename__ = "third_parties"

    code = Column(String, unique=True, nullable=False, default=generate_code)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
