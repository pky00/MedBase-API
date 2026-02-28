"""Tests for treatment endpoints."""
from datetime import datetime, date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.appointment import Appointment
from app.model.treatment import Treatment
from app.model.patient import Patient
from app.model.partner import Partner
from app.model.third_party import ThirdParty
from app.model.user import User


@pytest.fixture
async def patient(db_session: AsyncSession, admin_user: User) -> Patient:
    """Create a patient for testing."""
    tp = ThirdParty(name="Treat Patient", type="patient", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    patient = Patient(
        third_party_id=tp.id,
        first_name="Treat",
        last_name="Patient",
        gender="male",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient


@pytest.fixture
async def referral_partner(db_session: AsyncSession, admin_user: User) -> Partner:
    """Create a referral partner for testing."""
    tp = ThirdParty(name="Referral Hospital", type="partner", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    partner = Partner(
        third_party_id=tp.id,
        name="Referral Hospital",
        partner_type="referral",
        organization_type="hospital",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(partner)
    await db_session.commit()
    await db_session.refresh(partner)
    return partner


@pytest.fixture
async def donor_partner(db_session: AsyncSession, admin_user: User) -> Partner:
    """Create a donor-only partner for testing."""
    tp = ThirdParty(name="Donor Only", type="partner", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    partner = Partner(
        third_party_id=tp.id,
        name="Donor Only",
        partner_type="donor",
        organization_type="NGO",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(partner)
    await db_session.commit()
    await db_session.refresh(partner)
    return partner


@pytest.fixture
async def appointment(
    db_session: AsyncSession, admin_user: User, patient: Patient,
) -> Appointment:
    """Create an appointment for testing."""
    appt = Appointment(
        patient_id=patient.id,
        appointment_date=datetime(2026, 3, 1, 10, 0, 0),
        status="in_progress",
        type="scheduled",
        location="internal",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(appt)
    await db_session.commit()
    await db_session.refresh(appt)
    return appt


@pytest.fixture
async def treatment(
    db_session: AsyncSession, admin_user: User,
    patient: Patient, referral_partner: Partner, appointment: Appointment,
) -> Treatment:
    """Create a treatment for testing."""
    treatment = Treatment(
        patient_id=patient.id,
        appointment_id=appointment.id,
        partner_id=referral_partner.id,
        treatment_type="Surgery",
        description="Minor surgery",
        treatment_date=date(2026, 3, 5),
        status="pending",
        cost=500.00,
        notes="Requires local anesthesia",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(treatment)
    await db_session.commit()
    await db_session.refresh(treatment)
    return treatment


@pytest.fixture
async def second_treatment(
    db_session: AsyncSession, admin_user: User,
    patient: Patient, referral_partner: Partner,
) -> Treatment:
    """Create a second treatment for testing."""
    treatment = Treatment(
        patient_id=patient.id,
        partner_id=referral_partner.id,
        treatment_type="Physical Therapy",
        description="PT sessions",
        treatment_date=date(2026, 3, 10),
        status="pending",
        cost=200.00,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(treatment)
    await db_session.commit()
    await db_session.refresh(treatment)
    return treatment


class TestGetTreatments:
    """Tests for GET /api/v1/treatments"""

    @pytest.mark.asyncio
    async def test_get_treatments_authenticated(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
    ):
        """Test getting treatments list."""
        response = await client.get("/api/v1/treatments", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_treatments_unauthenticated(self, client: AsyncClient):
        """Test getting treatments without authentication."""
        response = await client.get("/api/v1/treatments")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_treatments_filter_by_status(
        self, client: AsyncClient, admin_headers: dict, treatment: Treatment,
    ):
        """Test filtering treatments by status."""
        response = await client.get(
            "/api/v1/treatments", params={"status": "pending"}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_treatments_filter_by_patient(
        self, client: AsyncClient, admin_headers: dict,
        treatment: Treatment, patient: Patient,
    ):
        """Test filtering treatments by patient_id."""
        response = await client.get(
            "/api/v1/treatments", params={"patient_id": patient.id}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["patient_id"] == patient.id

    @pytest.mark.asyncio
    async def test_get_treatments_filter_by_partner(
        self, client: AsyncClient, admin_headers: dict,
        treatment: Treatment, referral_partner: Partner,
    ):
        """Test filtering treatments by partner_id."""
        response = await client.get(
            "/api/v1/treatments", params={"partner_id": referral_partner.id}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["partner_id"] == referral_partner.id

    @pytest.mark.asyncio
    async def test_get_treatments_pagination(
        self, client: AsyncClient, admin_headers: dict,
        treatment: Treatment, second_treatment: Treatment,
    ):
        """Test pagination works correctly."""
        response = await client.get(
            "/api/v1/treatments", params={"page": 1, "size": 1}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_get_treatments_includes_names(
        self, client: AsyncClient, admin_headers: dict, treatment: Treatment,
    ):
        """Test that list response includes patient and partner names."""
        response = await client.get("/api/v1/treatments", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        item = data["items"][0]
        assert "patient_name" in item
        assert "partner_name" in item


class TestGetTreatment:
    """Tests for GET /api/v1/treatments/{id}"""

    @pytest.mark.asyncio
    async def test_get_treatment_by_id(
        self, client: AsyncClient, admin_headers: dict, treatment: Treatment,
    ):
        """Test getting treatment by ID."""
        response = await client.get(
            f"/api/v1/treatments/{treatment.id}", headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["treatment_type"] == "Surgery"
        assert data["description"] == "Minor surgery"
        assert data["status"] == "pending"
        assert "patient_name" in data
        assert "partner_name" in data

    @pytest.mark.asyncio
    async def test_get_treatment_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent treatment."""
        response = await client.get("/api/v1/treatments/99999", headers=admin_headers)
        assert response.status_code == 404


class TestCreateTreatment:
    """Tests for POST /api/v1/treatments"""

    @pytest.mark.asyncio
    async def test_create_treatment_success(
        self, client: AsyncClient, admin_headers: dict,
        patient: Patient, referral_partner: Partner, db_session: AsyncSession,
    ):
        """Test creating a treatment."""
        response = await client.post(
            "/api/v1/treatments",
            json={
                "patient_id": patient.id,
                "partner_id": referral_partner.id,
                "treatment_type": "X-Ray",
                "description": "Chest X-ray",
                "treatment_date": "2026-03-20",
                "cost": 150.00,
                "notes": "Standard procedure",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["patient_id"] == patient.id
        assert data["partner_id"] == referral_partner.id
        assert data["treatment_type"] == "X-Ray"
        assert data["status"] == "pending"

        # Verify in database
        result = await db_session.execute(
            select(Treatment).where(Treatment.id == data["id"])
        )
        db_treatment = result.scalar_one_or_none()
        assert db_treatment is not None
        assert db_treatment.treatment_type == "X-Ray"

    @pytest.mark.asyncio
    async def test_create_treatment_with_appointment(
        self, client: AsyncClient, admin_headers: dict,
        patient: Patient, referral_partner: Partner, appointment: Appointment,
    ):
        """Test creating a treatment linked to an appointment."""
        response = await client.post(
            "/api/v1/treatments",
            json={
                "patient_id": patient.id,
                "partner_id": referral_partner.id,
                "appointment_id": appointment.id,
                "treatment_type": "Lab Test",
                "treatment_date": "2026-03-15",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["appointment_id"] == appointment.id

    @pytest.mark.asyncio
    async def test_create_multiple_treatments_per_appointment(
        self, client: AsyncClient, admin_headers: dict,
        patient: Patient, referral_partner: Partner, appointment: Appointment,
    ):
        """Test that multiple treatments can be created per appointment."""
        # Create first treatment
        response1 = await client.post(
            "/api/v1/treatments",
            json={
                "patient_id": patient.id,
                "partner_id": referral_partner.id,
                "appointment_id": appointment.id,
                "treatment_type": "Lab Test",
            },
            headers=admin_headers,
        )
        assert response1.status_code == 201

        # Create second treatment for same appointment
        response2 = await client.post(
            "/api/v1/treatments",
            json={
                "patient_id": patient.id,
                "partner_id": referral_partner.id,
                "appointment_id": appointment.id,
                "treatment_type": "MRI Scan",
            },
            headers=admin_headers,
        )
        assert response2.status_code == 201

        # Both should exist
        assert response1.json()["id"] != response2.json()["id"]

    @pytest.mark.asyncio
    async def test_create_treatment_donor_partner_fails(
        self, client: AsyncClient, admin_headers: dict,
        patient: Patient, donor_partner: Partner,
    ):
        """Test that donor-only partner cannot be used for treatment."""
        response = await client.post(
            "/api/v1/treatments",
            json={
                "patient_id": patient.id,
                "partner_id": donor_partner.id,
                "treatment_type": "Surgery",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "referral" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_treatment_invalid_patient(
        self, client: AsyncClient, admin_headers: dict, referral_partner: Partner,
    ):
        """Test creating treatment with non-existent patient."""
        response = await client.post(
            "/api/v1/treatments",
            json={
                "patient_id": 99999,
                "partner_id": referral_partner.id,
                "treatment_type": "Surgery",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "Patient not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_treatment_invalid_partner(
        self, client: AsyncClient, admin_headers: dict, patient: Patient,
    ):
        """Test creating treatment with non-existent partner."""
        response = await client.post(
            "/api/v1/treatments",
            json={
                "patient_id": patient.id,
                "partner_id": 99999,
                "treatment_type": "Surgery",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "Partner not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_treatment_invalid_appointment(
        self, client: AsyncClient, admin_headers: dict,
        patient: Patient, referral_partner: Partner,
    ):
        """Test creating treatment with non-existent appointment."""
        response = await client.post(
            "/api/v1/treatments",
            json={
                "patient_id": patient.id,
                "partner_id": referral_partner.id,
                "appointment_id": 99999,
                "treatment_type": "Surgery",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "Appointment not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_treatment_empty_type_fails(
        self, client: AsyncClient, admin_headers: dict,
        patient: Patient, referral_partner: Partner,
    ):
        """Test creating treatment with empty type fails."""
        response = await client.post(
            "/api/v1/treatments",
            json={
                "patient_id": patient.id,
                "partner_id": referral_partner.id,
                "treatment_type": "",
            },
            headers=admin_headers,
        )
        assert response.status_code == 422


class TestUpdateTreatment:
    """Tests for PUT /api/v1/treatments/{id}"""

    @pytest.mark.asyncio
    async def test_update_treatment_success(
        self, client: AsyncClient, admin_headers: dict, treatment: Treatment,
    ):
        """Test updating a treatment."""
        response = await client.put(
            f"/api/v1/treatments/{treatment.id}",
            json={"description": "Updated description", "cost": 750.00},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert float(data["cost"]) == 750.00

    @pytest.mark.asyncio
    async def test_update_treatment_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent treatment."""
        response = await client.put(
            "/api/v1/treatments/99999",
            json={"description": "Test"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_treatment_invalid_partner_type(
        self, client: AsyncClient, admin_headers: dict,
        treatment: Treatment, donor_partner: Partner,
    ):
        """Test updating treatment with donor-only partner fails."""
        response = await client.put(
            f"/api/v1/treatments/{treatment.id}",
            json={"partner_id": donor_partner.id},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "referral" in response.json()["detail"].lower()


class TestUpdateTreatmentStatus:
    """Tests for PUT /api/v1/treatments/{id}/status"""

    @pytest.mark.asyncio
    async def test_update_status_to_completed(
        self, client: AsyncClient, admin_headers: dict, treatment: Treatment,
    ):
        """Test completing a treatment."""
        response = await client.put(
            f"/api/v1/treatments/{treatment.id}/status",
            json={"status": "completed"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_update_status_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating status of non-existent treatment."""
        response = await client.put(
            "/api/v1/treatments/99999/status",
            json={"status": "pending"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_status_invalid_value(
        self, client: AsyncClient, admin_headers: dict, treatment: Treatment,
    ):
        """Test updating status with invalid value."""
        response = await client.put(
            f"/api/v1/treatments/{treatment.id}/status",
            json={"status": "invalid_status"},
            headers=admin_headers,
        )
        assert response.status_code == 422


class TestDeleteTreatment:
    """Tests for DELETE /api/v1/treatments/{id}"""

    @pytest.mark.asyncio
    async def test_delete_treatment_success(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, treatment: Treatment,
    ):
        """Test deleting treatment (soft delete)."""
        treatment_id = treatment.id
        response = await client.delete(
            f"/api/v1/treatments/{treatment_id}", headers=admin_headers,
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        db_session.expire_all()
        result = await db_session.execute(
            select(Treatment).where(Treatment.id == treatment_id)
        )
        db_treatment = result.scalar_one_or_none()
        assert db_treatment.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_treatment_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent treatment."""
        response = await client.delete("/api/v1/treatments/99999", headers=admin_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_deleted_treatment_not_in_list(
        self, client: AsyncClient, admin_headers: dict, treatment: Treatment,
    ):
        """Test that deleted treatment is not returned in list."""
        await client.delete(f"/api/v1/treatments/{treatment.id}", headers=admin_headers)

        response = await client.get("/api/v1/treatments", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        treatment_ids = [t["id"] for t in data["items"]]
        assert treatment.id not in treatment_ids
