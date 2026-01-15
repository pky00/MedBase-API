import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.system_setting import SystemSetting


class TestSystemSettingEndpoints:
    """Test cases for system settings endpoints."""

    @pytest.mark.asyncio
    async def test_create_setting(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test creating a new system setting."""
        import uuid
        setting_data = {
            "setting_key": f"test_setting_{uuid.uuid4().hex[:8]}",
            "setting_value": "test_value",
            "setting_type": "string",
            "category": "test",
            "description": "A test setting",
        }
        response = await client.post(
            "/api/v1/system-settings/",
            json=setting_data,
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["setting_key"] == setting_data["setting_key"]
        assert data["setting_value"] == setting_data["setting_value"]

        # Verify in database
        result = await db_session.execute(select(SystemSetting).where(SystemSetting.id == data["id"]))
        setting = result.scalar_one_or_none()
        assert setting is not None

    @pytest.mark.asyncio
    async def test_create_setting_duplicate_key(self, client: AsyncClient, admin_headers: dict):
        """Test creating setting with duplicate key fails."""
        setting_data = {
            "setting_key": "duplicate_key_test",
            "setting_value": "value1",
        }
        await client.post("/api/v1/system-settings/", json=setting_data, headers=admin_headers)

        setting_data["setting_value"] = "value2"
        response = await client.post("/api/v1/system-settings/", json=setting_data, headers=admin_headers)
        assert response.status_code == 400
        assert "Setting key already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_settings(self, client: AsyncClient, admin_headers: dict):
        """Test listing system settings."""
        response = await client.get("/api/v1/system-settings/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_settings_filter_by_category(self, client: AsyncClient, admin_headers: dict):
        """Test filtering settings by category."""
        import uuid
        await client.post(
            "/api/v1/system-settings/",
            json={
                "setting_key": f"inventory_setting_{uuid.uuid4().hex[:8]}",
                "setting_value": "10",
                "category": "inventory",
            },
            headers=admin_headers,
        )

        response = await client.get(
            "/api/v1/system-settings/?category=inventory",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        for setting in data["data"]:
            assert setting["category"] == "inventory"

    @pytest.mark.asyncio
    async def test_get_setting_by_key(self, client: AsyncClient, admin_headers: dict):
        """Test getting a setting by key."""
        import uuid
        key = f"get_by_key_test_{uuid.uuid4().hex[:8]}"
        await client.post(
            "/api/v1/system-settings/",
            json={"setting_key": key, "setting_value": "test"},
            headers=admin_headers,
        )

        response = await client.get(f"/api/v1/system-settings/key/{key}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["setting_key"] == key

    @pytest.mark.asyncio
    async def test_update_setting(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test updating a system setting."""
        import uuid
        create_response = await client.post(
            "/api/v1/system-settings/",
            json={
                "setting_key": f"update_test_{uuid.uuid4().hex[:8]}",
                "setting_value": "old_value",
                "is_editable": True,
            },
            headers=admin_headers,
        )
        setting_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/system-settings/{setting_id}",
            json={"setting_value": "new_value"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["setting_value"] == "new_value"

    @pytest.mark.asyncio
    async def test_update_non_editable_setting_fails(self, client: AsyncClient, admin_headers: dict):
        """Test updating a non-editable setting fails."""
        import uuid
        create_response = await client.post(
            "/api/v1/system-settings/",
            json={
                "setting_key": f"non_editable_{uuid.uuid4().hex[:8]}",
                "setting_value": "locked",
                "is_editable": False,
            },
            headers=admin_headers,
        )
        setting_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/system-settings/{setting_id}",
            json={"setting_value": "try_to_change"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "not editable" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_setting(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test deleting a system setting."""
        import uuid
        create_response = await client.post(
            "/api/v1/system-settings/",
            json={"setting_key": f"delete_test_{uuid.uuid4().hex[:8]}", "setting_value": "delete_me"},
            headers=admin_headers,
        )
        setting_id = create_response.json()["id"]

        response = await client.delete(f"/api/v1/system-settings/{setting_id}", headers=admin_headers)
        assert response.status_code == 204

        # Verify deleted
        result = await db_session.execute(select(SystemSetting).where(SystemSetting.id == setting_id))
        assert result.scalar_one_or_none() is None

