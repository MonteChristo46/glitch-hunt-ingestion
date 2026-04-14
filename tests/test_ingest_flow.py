from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db, DatabaseManager
from app.models.enums import IngestStatus

# Create a mock for the db dependency
mock_db_manager = MagicMock(spec=DatabaseManager)
mock_db_manager.pool = MagicMock() # Mock the pool attribute

# Override the dependency
async def get_mock_db():
    return mock_db_manager

app.dependency_overrides[get_db] = get_mock_db

client = TestClient(app)

@patch("app.api.ingest.DeviceHandler")
@patch("app.api.ingest.StorageService")
@patch("app.api.ingest.get_redis_client")
def test_ingest_request_authorized(mock_get_redis, MockStorage, MockDeviceHandler):
    # Setup Redis Mock
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    
    # Setup Storage Mock
    mock_storage = MagicMock()
    MockStorage.return_value = mock_storage # This mocks the dependency injection? No, depends uses get_storage_service
    # Wait, the dependency in main.py is get_storage_service. 
    # But in the test we are patching the class or the dependency?
    # In `app.api.ingest`, we do `storage: StorageService = Depends(get_storage_service)`.
    # Let's override the dependency instead of patching the class for cleaner testing.
    pass

# Let's restart the mocking strategy to be cleaner using dependency overrides.

@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    mock.cache_handshake = AsyncMock()
    mock.get_handshake = AsyncMock()
    mock.push_event = AsyncMock()
    return mock

@pytest.fixture
def mock_storage():
    mock = MagicMock()
    # Returns url, key, expires_at
    mock.generate_presigned_url.return_value = ("http://s3.url", "s3/key", datetime.now())
    return mock

@pytest.fixture
def mock_device_handler():
    mock = AsyncMock()
    return mock

@pytest.fixture
def mock_image_handler():
    mock = AsyncMock()
    return mock

# We need to patch the Handlers where they are instantiated
# In ingest.py: `device_handler = DeviceHandler(db.pool)`
# So we must patch `app.api.ingest.DeviceHandler`

def test_ingest_request_flow(mock_redis, mock_storage):
    # Override dependencies
    app.dependency_overrides[get_db] = get_mock_db
    
    async def override_get_redis():
        return mock_redis
    
    def override_get_storage():
        return mock_storage
        
    app.dependency_overrides["get_redis_client"] = override_get_redis # String key doesn't work usually, need function obj
    from app.redis.client import get_redis_client
    app.dependency_overrides[get_redis_client] = override_get_redis
    
    from app.services.storage import get_storage_service
    app.dependency_overrides[get_storage_service] = override_get_storage

    payload = {
        "device_id": "test-device",
        "filename": "test.log",
        "file_size_bytes": 1024,
        "sha256_checksum": "a" * 64,
        "file_path_context": ["test"],
        "device_context": {"fw_version": "1.0.0"},
        "metadata": {},
        "timestamp": "2024-01-01T00:00:00Z"
    }

    # Patch the DeviceHandler class used inside the route
    with patch("app.api.ingest.DeviceHandler") as MockDeviceHandler:
        instance = MockDeviceHandler.return_value
        from app.models.device import DeviceRead
        from uuid import uuid4
        mock_device = DeviceRead(device_id="test-device", account_id=uuid4(), is_active=True)
        instance.get_by_id = AsyncMock(return_value=mock_device)

        response = client.post("/v1/ingest/request", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert "handshake_id" in data
        assert "upload_url" in data
        
        # Verify Storage called
        mock_storage.generate_presigned_url.assert_called_once()
        
        # Verify Redis called
        mock_redis.cache_handshake.assert_awaited_once()
        
        # Verify Device Check
        instance.get_by_id.assert_awaited_with("test-device")

def test_ingest_request_unauthorized(mock_redis):
    # Override dependencies
    app.dependency_overrides[get_db] = get_mock_db
    
    async def override_get_redis():
        return mock_redis
        
    from app.redis.client import get_redis_client
    app.dependency_overrides[get_redis_client] = override_get_redis

    payload = {
        "device_id": "banned-device",
        "filename": "test.log",
        "file_size_bytes": 1024,
        "sha256_checksum": "a" * 64,
        "file_path_context": ["test"],
        "device_context": {"fw_version": "1.0.0"},
        "metadata": {},
        "timestamp": "2024-01-01T00:00:00Z"
    }

    with patch("app.api.ingest.DeviceHandler") as MockDeviceHandler:
        instance = MockDeviceHandler.return_value
        instance.get_by_id = AsyncMock(return_value=None) # Unauthorized

        response = client.post("/v1/ingest/request", json=payload)
        
        assert response.status_code == 403
        instance.get_by_id.assert_awaited_with("banned-device")

def test_ingest_confirm_success(mock_redis):
    # Override dependencies
    app.dependency_overrides[get_db] = get_mock_db
    
    async def override_get_redis():
        return mock_redis
        
    from app.redis.client import get_redis_client
    app.dependency_overrides[get_redis_client] = override_get_redis

    # Setup Redis to return handshake data
    handshake_id = "12345678-1234-5678-1234-567812345678"
    mock_redis.get_handshake.return_value = {
        "device_id": "test-device",
        "timestamp": "2024-01-01T00:00:00Z",
        "metadata": {"s3_key": "path/to/image.jpg"},
        "device_context": {"foo": "bar"},
        "_server_start_time": 1000.0
    }

    payload = {
        "handshake_id": handshake_id,
        "status": "INGESTED"
    }

    # Patch ImageHandler
    with patch("app.api.ingest.ImageHandler") as MockImageHandler:
        instance = MockImageHandler.return_value
        instance.create = AsyncMock()

        response = client.post("/v1/ingest/confirm", json=payload)
        
        assert response.status_code == 200
        
        # Verify ImageHandler called
        instance.create.assert_awaited_once()
        call_args = instance.create.await_args[0][0] # First arg of first call
        
        assert call_args.device_id == "test-device"
        assert call_args.image_path == "path/to/image.jpg"
        assert call_args.context == {"foo": "bar"}
        assert call_args.status == "INGESTED"
        
        # Verify Redis Event Pushed
        mock_redis.push_event.assert_awaited_once()

def test_ingest_confirm_missing_key(mock_redis):
    # Test error handling when s3_key is missing
    app.dependency_overrides[get_db] = get_mock_db
    
    async def override_get_redis():
        return mock_redis
        
    from app.redis.client import get_redis_client
    app.dependency_overrides[get_redis_client] = override_get_redis

    handshake_id = "12345678-1234-5678-1234-567812345678"
    mock_redis.get_handshake.return_value = {
        "device_id": "test-device",
        "timestamp": "2024-01-01T00:00:00Z",
        "metadata": {}, # Missing s3_key
        "device_context": {"foo": "bar"}
    }

    payload = {
        "handshake_id": handshake_id,
        "status": "INGESTED"
    }

    with patch("app.api.ingest.ImageHandler") as MockImageHandler:
        response = client.post("/v1/ingest/confirm", json=payload)
        assert response.status_code == 500
        assert "s3_key missing" in response.json()["detail"]