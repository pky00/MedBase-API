"""Tests for patient document endpoints."""
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.patient import Patient
from app.model.patient_document import PatientDocument
from app.model.third_party import ThirdParty
from app.model.user import User
from app.schema.patient_document import PatientDocumentType


@pytest.fixture(autouse=True)
def mock_presigned_url():
    """Mock presigned URL generation for all tests."""
    async def fake_presigned(key, expires_in=300, download_filename=""):
        return f"https://fake-presigned-url/{key}?signed=true"

    with patch(
        "app.service.patient_document.storage.generate_presigned_url",
        side_effect=fake_presigned,
    ), patch(
        "app.service.patient.storage.generate_presigned_url",
        side_effect=fake_presigned,
    ):
        yield


@pytest.fixture
async def patient(db_session: AsyncSession, admin_user: User) -> Patient:
    """Create a patient for document testing."""
    tp = ThirdParty(name="Doc Patient", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    patient = Patient(
        third_party_id=tp.id,
        first_name="Doc",
        last_name="Patient",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient


@pytest.fixture
async def document(db_session: AsyncSession, admin_user: User, patient: Patient) -> PatientDocument:
    """Create a patient document for testing."""
    doc = PatientDocument(
        patient_id=patient.id,
        document_name="test_report.pdf",
        document_type="lab_report",
        file_path="1/abc123.pdf",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


@pytest.fixture
async def second_document(db_session: AsyncSession, admin_user: User, patient: Patient) -> PatientDocument:
    """Create a second patient document for testing."""
    doc = PatientDocument(
        patient_id=patient.id,
        document_name="xray_scan.jpg",
        document_type="imaging",
        file_path="1/def456.jpg",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


class TestGetPatientDocumentTypes:
    """Tests for GET /api/v1/patient-document-types"""

    @pytest.mark.asyncio
    async def test_get_document_types_authenticated(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test getting document types returns all enum values."""
        response = await client.get(
            "/api/v1/patient-document-types", headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == len(PatientDocumentType)
        values = [item["value"] for item in data]
        for doc_type in PatientDocumentType:
            assert doc_type.value in values
        # Verify label format
        for item in data:
            assert "value" in item
            assert "label" in item
            assert "_" not in item["label"]

    @pytest.mark.asyncio
    async def test_get_document_types_unauthenticated(self, client: AsyncClient):
        """Test getting document types without authentication."""
        response = await client.get("/api/v1/patient-document-types")
        assert response.status_code == 401


class TestGetPatientDocuments:
    """Tests for GET /api/v1/patients/{patient_id}/documents"""

    @pytest.mark.asyncio
    async def test_get_documents_authenticated(
        self, client: AsyncClient, admin_headers: dict, patient: Patient,
    ):
        """Test getting documents list for a patient."""
        response = await client.get(
            f"/api/v1/patients/{patient.id}/documents", headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_documents_unauthenticated(self, client: AsyncClient, patient: Patient):
        """Test getting documents without authentication."""
        response = await client.get(f"/api/v1/patients/{patient.id}/documents")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_documents_patient_not_found(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test getting documents for non-existent patient."""
        response = await client.get(
            "/api/v1/patients/99999/documents", headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_documents_with_items(
        self, client: AsyncClient, admin_headers: dict,
        patient: Patient, document: PatientDocument,
    ):
        """Test getting documents returns existing documents."""
        response = await client.get(
            f"/api/v1/patients/{patient.id}/documents", headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert data["items"][0]["document_name"] == "test_report.pdf"
        assert "file_url" in data["items"][0]

    @pytest.mark.asyncio
    async def test_get_documents_filter_by_type(
        self, client: AsyncClient, admin_headers: dict,
        patient: Patient, document: PatientDocument, second_document: PatientDocument,
    ):
        """Test filtering documents by document_type."""
        response = await client.get(
            f"/api/v1/patients/{patient.id}/documents",
            params={"document_type": "lab_report"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["document_type"] == "lab_report"

    @pytest.mark.asyncio
    async def test_get_documents_pagination(
        self, client: AsyncClient, admin_headers: dict,
        patient: Patient, document: PatientDocument, second_document: PatientDocument,
    ):
        """Test pagination works correctly."""
        response = await client.get(
            f"/api/v1/patients/{patient.id}/documents",
            params={"page": 1, "size": 1},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] >= 2


class TestGetPatientDocument:
    """Tests for GET /api/v1/patient-documents/{id}"""

    @pytest.mark.asyncio
    async def test_get_document_by_id(
        self, client: AsyncClient, admin_headers: dict, document: PatientDocument,
    ):
        """Test getting document by ID."""
        response = await client.get(
            f"/api/v1/patient-documents/{document.id}", headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_name"] == "test_report.pdf"
        assert data["document_type"] == "lab_report"
        assert "file_url" in data
        assert "file_path" in data

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent document."""
        response = await client.get(
            "/api/v1/patient-documents/99999", headers=admin_headers,
        )
        assert response.status_code == 404


class TestUploadPatientDocument:
    """Tests for POST /api/v1/patients/{patient_id}/documents"""

    @pytest.mark.asyncio
    @patch("app.service.patient_document.storage.upload_file", new_callable=AsyncMock)
    async def test_upload_document_success(
        self, mock_upload, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, patient: Patient,
    ):
        """Test uploading a document for a patient."""
        mock_upload.return_value = "1/test.pdf"

        response = await client.post(
            f"/api/v1/patients/{patient.id}/documents",
            files={"file": ("report.pdf", b"fake pdf content", "application/pdf")},
            data={"document_type": "lab_report"},
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["document_name"] == "report.pdf"
        assert data["document_type"] == "lab_report"
        assert data["patient_id"] == patient.id
        assert "file_path" in data
        assert "file_url" in data

        # Verify stored in database
        result = await db_session.execute(
            select(PatientDocument).where(PatientDocument.id == data["id"])
        )
        doc = result.scalar_one_or_none()
        assert doc is not None
        assert doc.patient_id == patient.id

    @pytest.mark.asyncio
    @patch("app.service.patient_document.storage.upload_file", new_callable=AsyncMock)
    async def test_upload_document_without_type(
        self, mock_upload, client: AsyncClient, admin_headers: dict, patient: Patient,
    ):
        """Test uploading a document without document_type."""
        mock_upload.return_value = "1/test.jpg"

        response = await client.post(
            f"/api/v1/patients/{patient.id}/documents",
            files={"file": ("scan.jpg", b"fake image", "image/jpeg")},
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["document_type"] is None

    @pytest.mark.asyncio
    @patch("app.service.patient_document.storage.upload_file", new_callable=AsyncMock)
    async def test_upload_document_with_custom_name(
        self, mock_upload, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, patient: Patient,
    ):
        """Test uploading a document with a custom document_name."""
        mock_upload.return_value = "1/test.pdf"

        response = await client.post(
            f"/api/v1/patients/{patient.id}/documents",
            files={"file": ("report.pdf", b"fake pdf content", "application/pdf")},
            data={"document_name": "Blood Test Results", "document_type": "lab_report"},
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["document_name"] == "Blood Test Results"

        # Verify stored in database
        result = await db_session.execute(
            select(PatientDocument).where(PatientDocument.id == data["id"])
        )
        doc = result.scalar_one_or_none()
        assert doc is not None
        assert doc.document_name == "Blood Test Results"

    @pytest.mark.asyncio
    @patch("app.service.patient_document.storage.upload_file", new_callable=AsyncMock)
    async def test_upload_document_patient_not_found(
        self, mock_upload, client: AsyncClient, admin_headers: dict,
    ):
        """Test uploading document for non-existent patient."""
        response = await client.post(
            "/api/v1/patients/99999/documents",
            files={"file": ("test.pdf", b"content", "application/pdf")},
            headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_document_unauthenticated(self, client: AsyncClient, patient: Patient):
        """Test uploading document without authentication."""
        response = await client.post(
            f"/api/v1/patients/{patient.id}/documents",
            files={"file": ("test.pdf", b"content", "application/pdf")},
        )
        assert response.status_code == 401


class TestDeletePatientDocument:
    """Tests for DELETE /api/v1/patient-documents/{id}"""

    @pytest.mark.asyncio
    @patch("app.service.patient_document.storage.delete_file", new_callable=AsyncMock)
    async def test_delete_document_success(
        self, mock_delete, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, document: PatientDocument,
    ):
        """Test deleting document (soft delete)."""
        doc_id = document.id
        response = await client.delete(
            f"/api/v1/patient-documents/{doc_id}", headers=admin_headers,
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        db_session.expire_all()
        result = await db_session.execute(
            select(PatientDocument).where(PatientDocument.id == doc_id)
        )
        db_doc = result.scalar_one_or_none()
        assert db_doc.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent document."""
        response = await client.delete(
            "/api/v1/patient-documents/99999", headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("app.service.patient_document.storage.delete_file", new_callable=AsyncMock)
    async def test_deleted_document_not_in_list(
        self, mock_delete, client: AsyncClient, admin_headers: dict,
        patient: Patient, document: PatientDocument,
    ):
        """Test that deleted document is not returned in list."""
        await client.delete(
            f"/api/v1/patient-documents/{document.id}", headers=admin_headers,
        )

        response = await client.get(
            f"/api/v1/patients/{patient.id}/documents", headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        doc_ids = [d["id"] for d in data["items"]]
        assert document.id not in doc_ids
