import logging
import uuid
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import UploadFile

from app.model.patient_document import PatientDocument
from app.utility import storage

logger = logging.getLogger("medbase.service.patient_document")


class PatientDocumentService:
    """Service layer for patient document operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, document_id: int) -> Optional[PatientDocument]:
        """Get patient document by ID."""
        result = await self.db.execute(
            select(PatientDocument).where(
                PatientDocument.id == document_id,
                PatientDocument.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_for_patient(
        self,
        patient_id: int,
        page: int = 1,
        size: int = 10,
        document_type: Optional[str] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[PatientDocument], int]:
        """Get all documents for a patient with pagination and filtering."""
        query = select(PatientDocument).where(
            PatientDocument.patient_id == patient_id,
            PatientDocument.is_deleted == False,
        )

        if document_type is not None:
            query = query.where(PatientDocument.document_type == document_type)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        sort_column = getattr(PatientDocument, sort, PatientDocument.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        documents = result.scalars().all()

        logger.debug("Queried patient documents: patient_id=%d total=%d returned=%d", patient_id, total, len(documents))
        return list(documents), total

    async def upload(
        self,
        patient_id: int,
        file: UploadFile,
        document_type: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> PatientDocument:
        """Upload a document for a patient."""
        # Generate unique file key
        ext = ""
        if file.filename and "." in file.filename:
            ext = file.filename.rsplit(".", 1)[-1]
        unique_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
        file_key = f"patient-documents/{patient_id}/{unique_name}"

        # Read file content and upload to storage
        content = await file.read()
        content_type = file.content_type or "application/octet-stream"
        await storage.upload_file(file_key, content, content_type)

        document_name = file.filename or unique_name

        doc = PatientDocument(
            patient_id=patient_id,
            document_name=document_name,
            document_type=document_type,
            file_path=file_key,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)

        logger.info("Uploaded document id=%d patient_id=%d file_key='%s'", doc.id, patient_id, file_key)
        return doc

    async def delete(self, document_id: int, deleted_by: Optional[str] = None) -> bool:
        """Soft delete a patient document and remove from storage."""
        doc = await self.get_by_id(document_id)
        if not doc:
            return False

        # Delete from storage
        try:
            await storage.delete_file(doc.file_path)
        except Exception as e:
            logger.warning("Failed to delete file from storage key='%s': %s", doc.file_path, str(e))

        doc.is_deleted = True
        doc.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted document id=%d", document_id)
        return True
