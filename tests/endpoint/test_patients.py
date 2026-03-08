"""Tests for patient endpoints."""
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.patient import Patient
from app.model.third_party import ThirdParty
from app.model.user import User


@pytest.fixture
async def patient(db_session: AsyncSession, admin_user: User) -> Patient:
    """Create a patient for testing."""
    tp = ThirdParty(name="John Doe", phone="1234567890", email="john.doe@test.com", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    patient = Patient(
        third_party_id=tp.id,
        date_of_birth=date(1990, 5, 15),
        gender="male",
        address="123 Main St",
        emergency_contact="Jane Doe",
        emergency_phone="0987654321",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    patient.third_party = tp
    return patient


@pytest.fixture
async def second_patient(db_session: AsyncSession, admin_user: User) -> Patient:
    """Create a second patient for testing."""
    tp = ThirdParty(name="Jane Smith", phone="5555555555", email="jane.smith@test.com", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    patient = Patient(
        third_party_id=tp.id,
        date_of_birth=date(1985, 3, 20),
        gender="female",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    patient.third_party = tp
    return patient


class TestGetPatients:
    """Tests for GET /api/v1/patients"""

    @pytest.mark.asyncio
    async def test_get_patients_authenticated(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
    ):
        """Test getting patients list."""
        response = await client.get("/api/v1/patients", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_patients_unauthenticated(self, client: AsyncClient):
        """Test getting patients without authentication."""
        response = await client.get("/api/v1/patients")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_patients_filter_by_gender(
        self, client: AsyncClient, admin_headers: dict, patient: Patient,
    ):
        """Test filtering patients by gender."""
        response = await client.get(
            "/api/v1/patients", params={"gender": "male"}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["gender"] == "male"

    @pytest.mark.asyncio
    async def test_get_patients_filter_by_is_active(
        self, client: AsyncClient, admin_headers: dict, patient: Patient,
    ):
        """Test filtering patients by is_active."""
        response = await client.get(
            "/api/v1/patients", params={"is_active": True}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_patients_with_search(
        self, client: AsyncClient, admin_headers: dict, patient: Patient,
    ):
        """Test searching patients by name."""
        response = await client.get(
            "/api/v1/patients", params={"search": "John"}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_patients_search_by_name(
        self, client: AsyncClient, admin_headers: dict, patient: Patient,
    ):
        """Test searching patients by name."""
        response = await client.get(
            "/api/v1/patients", params={"search": "Doe"}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_patients_pagination(
        self, client: AsyncClient, admin_headers: dict,
        patient: Patient, second_patient: Patient,
    ):
        """Test pagination works correctly."""
        response = await client.get(
            "/api/v1/patients", params={"page": 1, "size": 1}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] >= 2


class TestGetPatient:
    """Tests for GET /api/v1/patients/{id}"""

    @pytest.mark.asyncio
    async def test_get_patient_by_id(
        self, client: AsyncClient, admin_headers: dict, patient: Patient,
    ):
        """Test getting patient by ID."""
        response = await client.get(
            f"/api/v1/patients/{patient.id}", headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["gender"] == "male"
        assert "third_party_id" in data
        assert data["third_party"]["name"] == "John Doe"
        assert data["third_party"]["phone"] == "1234567890"

    @pytest.mark.asyncio
    async def test_get_patient_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent patient."""
        response = await client.get("/api/v1/patients/99999", headers=admin_headers)
        assert response.status_code == 404


class TestCreatePatient:
    """Tests for POST /api/v1/patients"""

    @pytest.mark.asyncio
    async def test_create_patient_auto_creates_third_party(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test creating a patient auto-creates a third_party record."""
        response = await client.post(
            "/api/v1/patients",
            json={
                "name": "New Patient",
                "gender": "female",
                "phone": "111222333",
                "email": "new.patient@test.com",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["gender"] == "female"
        assert "third_party_id" in data
        assert data["third_party"]["name"] == "New Patient"
        assert data["third_party"]["phone"] == "111222333"

        # Verify third_party was created
        result = await db_session.execute(
            select(ThirdParty).where(ThirdParty.id == data["third_party_id"])
        )
        tp = result.scalar_one_or_none()
        assert tp is not None
        assert tp.name == "New Patient"

    @pytest.mark.asyncio
    async def test_create_patient_with_all_fields(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating a patient with all fields."""
        response = await client.post(
            "/api/v1/patients",
            json={
                "name": "Full Record",
                "date_of_birth": "2000-01-01",
                "gender": "male",
                "phone": "444555666",
                "email": "full.record@test.com",
                "address": "456 Oak Ave",
                "emergency_contact": "Emergency Person",
                "emergency_phone": "777888999",
                "is_active": True,
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["date_of_birth"] == "2000-01-01"
        assert data["address"] == "456 Oak Ave"
        assert data["emergency_contact"] == "Emergency Person"
        assert data["emergency_phone"] == "777888999"

    @pytest.mark.asyncio
    async def test_create_patient_minimal_fields(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating a patient with only required fields."""
        response = await client.post(
            "/api/v1/patients",
            json={"name": "Minimal Patient"},
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["third_party"]["name"] == "Minimal Patient"
        assert data["gender"] is None

    @pytest.mark.asyncio
    async def test_create_patient_duplicate_name(
        self, client: AsyncClient, admin_headers: dict, patient: Patient,
    ):
        """Test creating patient with duplicate name fails."""
        response = await client.post(
            "/api/v1/patients",
            json={"name": "John Doe"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "Patient name already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_patient_duplicate_name_in_third_parties(
        self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession,
    ):
        """Test creating patient with name that already exists in third_parties fails."""
        tp = ThirdParty(name="Existing TP Patient", is_active=True)
        db_session.add(tp)
        await db_session.commit()

        response = await client.post(
            "/api/v1/patients",
            json={"name": "Existing TP Patient"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already exists in third parties" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_patient_no_name_no_third_party(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating patient without name and without third_party_id fails."""
        response = await client.post(
            "/api/v1/patients",
            json={"gender": "male"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "Name is required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_patient_with_existing_third_party(
        self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession,
    ):
        """Test creating a patient with an existing third_party_id."""
        tp = ThirdParty(name="Pre-existing TP", is_active=True)
        db_session.add(tp)
        await db_session.commit()
        await db_session.refresh(tp)

        response = await client.post(
            "/api/v1/patients",
            json={
                "third_party_id": tp.id,
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["third_party_id"] == tp.id

    @pytest.mark.asyncio
    async def test_create_patient_invalid_third_party(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating patient with non-existent third_party_id fails."""
        response = await client.post(
            "/api/v1/patients",
            json={
                "third_party_id": 99999,
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "Third party not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_patient_invalid_gender(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating patient with invalid gender fails."""
        response = await client.post(
            "/api/v1/patients",
            json={
                "name": "Bad Gender",
                "gender": "invalid",
            },
            headers=admin_headers,
        )
        assert response.status_code == 422


class TestUpdatePatient:
    """Tests for PUT /api/v1/patients/{id}"""

    @pytest.mark.asyncio
    async def test_update_patient_success(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, patient: Patient,
    ):
        """Test updating a patient."""
        response = await client.put(
            f"/api/v1/patients/{patient.id}",
            json={"address": "456 New Address"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == "456 New Address"

    @pytest.mark.asyncio
    async def test_update_patient_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent patient."""
        response = await client.put(
            "/api/v1/patients/99999", json={"address": "Test"}, headers=admin_headers,
        )
        assert response.status_code == 404


class TestDeletePatient:
    """Tests for DELETE /api/v1/patients/{id}"""

    @pytest.mark.asyncio
    async def test_delete_patient_success(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, patient: Patient,
    ):
        """Test deleting patient (soft delete)."""
        patient_id = patient.id
        response = await client.delete(
            f"/api/v1/patients/{patient_id}", headers=admin_headers,
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        db_session.expire_all()
        result = await db_session.execute(
            select(Patient).where(Patient.id == patient_id)
        )
        db_patient = result.scalar_one_or_none()
        assert db_patient.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_patient_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent patient."""
        response = await client.delete("/api/v1/patients/99999", headers=admin_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_deleted_patient_not_in_list(
        self, client: AsyncClient, admin_headers: dict, patient: Patient,
    ):
        """Test that deleted patient is not returned in list."""
        # Delete the patient
        await client.delete(f"/api/v1/patients/{patient.id}", headers=admin_headers)

        # Verify it's not in the list
        response = await client.get("/api/v1/patients", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        patient_ids = [p["id"] for p in data["items"]]
        assert patient.id not in patient_ids
