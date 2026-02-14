"""Tests for donation and donation item endpoints."""
import pytest
from datetime import date
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.partner import Partner
from app.model.donation import Donation, DonationItem
from app.model.medicine import Medicine
from app.model.equipment import Equipment
from app.model.medical_device import MedicalDevice
from app.model.inventory import Inventory
from app.model.user import User


@pytest.fixture
async def donor_partner(db_session: AsyncSession, admin_user: User) -> Partner:
    """Create a donor partner for testing."""
    partner = Partner(
        name="Donation Test Donor",
        partner_type="donor",
        organization_type="NGO",
        is_active=True,
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(partner)
    await db_session.commit()
    await db_session.refresh(partner)
    return partner


@pytest.fixture
async def referral_partner(db_session: AsyncSession, admin_user: User) -> Partner:
    """Create a referral-only partner for testing."""
    partner = Partner(
        name="Referral Only Partner",
        partner_type="referral",
        organization_type="hospital",
        is_active=True,
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(partner)
    await db_session.commit()
    await db_session.refresh(partner)
    return partner


@pytest.fixture
async def medicine_with_inventory(db_session: AsyncSession, admin_user: User):
    """Create a medicine with an inventory record."""
    med = Medicine(
        name="Test Medicine",
        description="For donation tests",
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(med)
    await db_session.flush()
    await db_session.refresh(med)

    inv = Inventory(
        item_type="medicine",
        item_id=med.id,
        quantity=0,
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(inv)
    await db_session.commit()
    await db_session.refresh(med)
    await db_session.refresh(inv)
    return med, inv


@pytest.fixture
async def equipment_with_inventory(db_session: AsyncSession, admin_user: User):
    """Create equipment with an inventory record."""
    eq = Equipment(
        name="Test Equipment",
        condition="new",
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(eq)
    await db_session.flush()
    await db_session.refresh(eq)

    inv = Inventory(
        item_type="equipment",
        item_id=eq.id,
        quantity=0,
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(inv)
    await db_session.commit()
    await db_session.refresh(eq)
    await db_session.refresh(inv)
    return eq, inv


@pytest.fixture
async def donation(
    db_session: AsyncSession, admin_user: User, donor_partner: Partner
) -> Donation:
    """Create a donation for testing."""
    d = Donation(
        partner_id=donor_partner.id,
        donation_date=date(2026, 1, 15),
        notes="Test donation",
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


class TestGetDonations:
    """Tests for GET /api/v1/donations"""

    @pytest.mark.asyncio
    async def test_get_donations_authenticated(
        self, client: AsyncClient, admin_user: User, admin_headers: dict
    ):
        """Test getting donations list."""
        response = await client.get("/api/v1/donations", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_donations_unauthenticated(self, client: AsyncClient):
        """Test getting donations without authentication."""
        response = await client.get("/api/v1/donations")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_donations_filter_by_partner(
        self, client: AsyncClient, admin_headers: dict,
        donation: Donation, donor_partner: Partner,
    ):
        """Test filtering donations by partner_id."""
        response = await client.get(
            "/api/v1/donations",
            params={"partner_id": donor_partner.id},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["partner_id"] == donor_partner.id

    @pytest.mark.asyncio
    async def test_get_donations_filter_by_date(
        self, client: AsyncClient, admin_headers: dict,
        donation: Donation,
    ):
        """Test filtering donations by donation_date."""
        response = await client.get(
            "/api/v1/donations",
            params={"donation_date": "2026-01-15"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_donations_includes_partner_name(
        self, client: AsyncClient, admin_headers: dict,
        donation: Donation, donor_partner: Partner,
    ):
        """Test that donations list includes partner_name."""
        response = await client.get("/api/v1/donations", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        found = False
        for item in data["items"]:
            if item["id"] == donation.id:
                assert item["partner_name"] == donor_partner.name
                found = True
        assert found


class TestGetDonation:
    """Tests for GET /api/v1/donations/{id}"""

    @pytest.mark.asyncio
    async def test_get_donation_with_items(
        self, client: AsyncClient, admin_headers: dict,
        donation: Donation,
    ):
        """Test getting donation by ID includes items."""
        response = await client.get(
            f"/api/v1/donations/{donation.id}", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == donation.id
        assert "items" in data
        assert "partner_name" in data

    @pytest.mark.asyncio
    async def test_get_donation_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent donation."""
        response = await client.get(
            "/api/v1/donations/99999", headers=admin_headers
        )
        assert response.status_code == 404


class TestCreateDonation:
    """Tests for POST /api/v1/donations"""

    @pytest.mark.asyncio
    async def test_create_donation_without_items(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, donor_partner: Partner,
    ):
        """Test creating a donation without items."""
        donation_data = {
            "partner_id": donor_partner.id,
            "donation_date": "2026-02-10",
            "notes": "Test donation",
        }

        response = await client.post(
            "/api/v1/donations",
            json=donation_data,
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["partner_id"] == donor_partner.id
        assert data["donation_date"] == "2026-02-10"

        # Verify in database
        result = await db_session.execute(
            select(Donation).where(Donation.id == data["id"])
        )
        db_donation = result.scalar_one_or_none()
        assert db_donation is not None
        assert db_donation.created_by == admin_user.id

    @pytest.mark.asyncio
    async def test_create_donation_with_items(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, donor_partner: Partner,
        medicine_with_inventory,
    ):
        """Test creating a donation with items and verify inventory update."""
        med, inv = medicine_with_inventory
        initial_qty = inv.quantity

        donation_data = {
            "partner_id": donor_partner.id,
            "donation_date": "2026-02-10",
            "notes": "Donation with items",
            "items": [
                {
                    "item_type": "medicine",
                    "item_id": med.id,
                    "quantity": 50,
                }
            ],
        }

        response = await client.post(
            "/api/v1/donations",
            json=donation_data,
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["partner_id"] == donor_partner.id

        # Verify donation items were created
        result = await db_session.execute(
            select(DonationItem).where(
                DonationItem.donation_id == data["id"],
                DonationItem.is_deleted == False,
            )
        )
        items = result.scalars().all()
        assert len(items) == 1
        assert items[0].item_type == "medicine"
        assert items[0].quantity == 50

        # Verify inventory was updated
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == med.id,
            )
        )
        updated_inv = result.scalar_one_or_none()
        assert updated_inv.quantity == initial_qty + 50

    @pytest.mark.asyncio
    async def test_create_donation_non_donor_partner(
        self, client: AsyncClient, admin_headers: dict,
        referral_partner: Partner,
    ):
        """Test creating donation with referral-only partner fails."""
        response = await client.post(
            "/api/v1/donations",
            json={
                "partner_id": referral_partner.id,
                "donation_date": "2026-02-10",
            },
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "donor" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_donation_invalid_partner(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating donation with non-existent partner fails."""
        response = await client.post(
            "/api/v1/donations",
            json={
                "partner_id": 99999,
                "donation_date": "2026-02-10",
            },
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "Partner not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_donation_invalid_item(
        self, client: AsyncClient, admin_headers: dict,
        donor_partner: Partner,
    ):
        """Test creating donation with invalid item fails."""
        response = await client.post(
            "/api/v1/donations",
            json={
                "partner_id": donor_partner.id,
                "donation_date": "2026-02-10",
                "items": [
                    {"item_type": "medicine", "item_id": 99999, "quantity": 10}
                ],
            },
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "Item not found" in response.json()["detail"]


class TestUpdateDonation:
    """Tests for PUT /api/v1/donations/{id}"""

    @pytest.mark.asyncio
    async def test_update_donation_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, donation: Donation,
    ):
        """Test updating a donation and verify in database."""
        response = await client.put(
            f"/api/v1/donations/{donation.id}",
            json={"notes": "Updated notes", "donation_date": "2026-03-01"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes"
        assert data["donation_date"] == "2026-03-01"

        # Verify in database
        db_session.expire_all()
        result = await db_session.execute(
            select(Donation).where(Donation.id == donation.id)
        )
        db_donation = result.scalar_one_or_none()
        assert db_donation.notes == "Updated notes"
        assert db_donation.updated_by == admin_user.id

    @pytest.mark.asyncio
    async def test_update_donation_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent donation."""
        response = await client.put(
            "/api/v1/donations/99999",
            json={"notes": "Test"},
            headers=admin_headers,
        )
        assert response.status_code == 404


class TestDeleteDonation:
    """Tests for DELETE /api/v1/donations/{id}"""

    @pytest.mark.asyncio
    async def test_delete_donation_reverses_inventory(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, donor_partner: Partner,
        medicine_with_inventory,
    ):
        """Test deleting donation soft-deletes items and reverses inventory."""
        med, inv = medicine_with_inventory

        # Create donation with items via API
        response = await client.post(
            "/api/v1/donations",
            json={
                "partner_id": donor_partner.id,
                "donation_date": "2026-02-10",
                "items": [
                    {"item_type": "medicine", "item_id": med.id, "quantity": 30}
                ],
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        donation_id = response.json()["id"]

        # Verify inventory increased
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == med.id,
            )
        )
        inv_record = result.scalar_one_or_none()
        assert inv_record.quantity == 30

        # Delete donation
        response = await client.delete(
            f"/api/v1/donations/{donation_id}", headers=admin_headers
        )
        assert response.status_code == 200

        # Verify donation soft deleted
        db_session.expire_all()
        result = await db_session.execute(
            select(Donation).where(Donation.id == donation_id)
        )
        db_donation = result.scalar_one_or_none()
        assert db_donation.is_deleted is True

        # Verify items soft deleted
        result = await db_session.execute(
            select(DonationItem).where(DonationItem.donation_id == donation_id)
        )
        items = result.scalars().all()
        for item in items:
            assert item.is_deleted is True

        # Verify inventory reversed
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == med.id,
            )
        )
        inv_after = result.scalar_one_or_none()
        assert inv_after.quantity == 0

    @pytest.mark.asyncio
    async def test_delete_donation_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent donation."""
        response = await client.delete(
            "/api/v1/donations/99999", headers=admin_headers
        )
        assert response.status_code == 404


class TestDonationItems:
    """Tests for donation item endpoints."""

    @pytest.mark.asyncio
    async def test_get_donation_items(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, donation: Donation,
        medicine_with_inventory,
    ):
        """Test getting items for a donation."""
        med, _ = medicine_with_inventory

        # Add item directly to DB
        item = DonationItem(
            donation_id=donation.id,
            item_type="medicine",
            item_id=med.id,
            quantity=10,
            created_by=admin_user.id,
            updated_by=admin_user.id,
        )
        db_session.add(item)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/donations/{donation.id}/items",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["item_type"] == "medicine"
        assert data[0]["item_name"] == "Test Medicine"

    @pytest.mark.asyncio
    async def test_add_item_to_donation(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, donation: Donation,
        medicine_with_inventory,
    ):
        """Test adding an item to a donation updates inventory."""
        med, inv = medicine_with_inventory
        initial_qty = inv.quantity

        response = await client.post(
            f"/api/v1/donations/{donation.id}/items",
            json={
                "item_type": "medicine",
                "item_id": med.id,
                "quantity": 25,
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["item_type"] == "medicine"
        assert data["quantity"] == 25
        assert data["item_name"] == "Test Medicine"

        # Verify inventory updated
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == med.id,
            )
        )
        updated_inv = result.scalar_one_or_none()
        assert updated_inv.quantity == initial_qty + 25

    @pytest.mark.asyncio
    async def test_add_item_invalid_item(
        self, client: AsyncClient, admin_headers: dict,
        donation: Donation,
    ):
        """Test adding invalid item to donation fails."""
        response = await client.post(
            f"/api/v1/donations/{donation.id}/items",
            json={
                "item_type": "medicine",
                "item_id": 99999,
                "quantity": 10,
            },
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "Item not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_add_item_donation_not_found(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test adding item to non-existent donation fails."""
        response = await client.post(
            "/api/v1/donations/99999/items",
            json={
                "item_type": "medicine",
                "item_id": 1,
                "quantity": 10,
            },
            headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_donation_item(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, donation: Donation,
        medicine_with_inventory,
    ):
        """Test updating a donation item adjusts inventory."""
        med, inv = medicine_with_inventory

        # Add item via API
        response = await client.post(
            f"/api/v1/donations/{donation.id}/items",
            json={
                "item_type": "medicine",
                "item_id": med.id,
                "quantity": 20,
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        item_id = response.json()["id"]

        # Update quantity
        response = await client.put(
            f"/api/v1/donation-items/{item_id}",
            json={"quantity": 30},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 30

        # Verify inventory adjusted (was +20, now should be +30 total)
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == med.id,
            )
        )
        updated_inv = result.scalar_one_or_none()
        assert updated_inv.quantity == 30

    @pytest.mark.asyncio
    async def test_delete_donation_item(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, donation: Donation,
        medicine_with_inventory,
    ):
        """Test deleting a donation item reverses inventory."""
        med, inv = medicine_with_inventory

        # Add item via API
        response = await client.post(
            f"/api/v1/donations/{donation.id}/items",
            json={
                "item_type": "medicine",
                "item_id": med.id,
                "quantity": 15,
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        item_id = response.json()["id"]

        # Verify inventory increased
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == med.id,
            )
        )
        assert result.scalar_one_or_none().quantity == 15

        # Delete item
        response = await client.delete(
            f"/api/v1/donation-items/{item_id}",
            headers=admin_headers,
        )
        assert response.status_code == 200

        # Verify inventory reversed
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == med.id,
            )
        )
        assert result.scalar_one_or_none().quantity == 0

    @pytest.mark.asyncio
    async def test_delete_donation_item_not_found(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test deleting non-existent donation item."""
        response = await client.delete(
            "/api/v1/donation-items/99999",
            headers=admin_headers,
        )
        assert response.status_code == 404
