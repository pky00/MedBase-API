import logging
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.patient_document import PatientDocument
from app.models.enums import DocumentType
from app.schemas.patient_document import PatientDocumentCreate, PatientDocumentUpdate

logger = logging.getLogger(__name__)


class PatientDocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, document_id: UUID) -> PatientDocument | None:
        result = await self.db.execute(
            select(PatientDocument).where(PatientDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def list_by_patient(
        self,
        patient_id: UUID,
        document_type: DocumentType | None = None,
    ) -> tuple[list[PatientDocument], int]:
        logger.info(f"Listing documents for patient: {patient_id}")
        query = select(PatientDocument).where(PatientDocument.patient_id == patient_id)
        count_query = select(func.count(PatientDocument.id)).where(
            PatientDocument.patient_id == patient_id
        )

        if document_type:
            query = query.where(PatientDocument.document_type == document_type)
            count_query = count_query.where(PatientDocument.document_type == document_type)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        query = query.order_by(PatientDocument.upload_date.desc())
        result = await self.db.execute(query)
        documents = list(result.scalars().all())
        return documents, total

    async def create(self, data: PatientDocumentCreate, created_by: str) -> PatientDocument:
        logger.info(f"Creating document for patient: {data.patient_id}")
        document = PatientDocument(
            **data.model_dump(),
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def update(
        self, document: PatientDocument, data: PatientDocumentUpdate, updated_by: str
    ) -> PatientDocument:
        logger.info(f"Updating document: {document.id}")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(document, field, value)
        document.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def delete(self, document: PatientDocument) -> None:
        logger.info(f"Deleting document: {document.id}")
        await self.db.delete(document)
        await self.db.commit()

