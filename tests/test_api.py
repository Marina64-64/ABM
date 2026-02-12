"""
Unit tests for Task 2 API components.
"""

import pytest
from fastapi.testclient import TestClient
from src.task2_api.app import app
from src.task2_api.models import TaskStatus


client = TestClient(app)


class TestAPIEndpoints:
    """Test API endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_submit_task_valid(self):
        """Test submitting valid reCAPTCHA task."""
        payload = {
            "sitekey": "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-",
            "pageurl": "https://www.google.com/recaptcha/api2/demo"
        }
        
        response = client.post("/recaptcha/in", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "taskId" in data
        assert data["status"] == TaskStatus.PROCESSING
    
    def test_submit_task_invalid(self):
        """Test submitting invalid task (missing fields)."""
        payload = {
            "sitekey": "test-key"
            # Missing pageurl
        }
        
        response = client.post("/recaptcha/in", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_get_result_not_found(self):
        """Test getting result for non-existent task."""
        response = client.get("/recaptcha/res?taskId=nonexistent-id")
        assert response.status_code == 404
    
    def test_get_result_processing(self):
        """Test getting result for processing task."""
        # First submit a task
        payload = {
            "sitekey": "test-key",
            "pageurl": "https://example.com"
        }
        submit_response = client.post("/recaptcha/in", json=payload)
        task_id = submit_response.json()["taskId"]
        
        # Then get result (should be processing)
        response = client.get(f"/recaptcha/res?taskId={task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["taskId"] == task_id
        # Status could be processing or ready depending on timing


class TestModels:
    """Test Pydantic models."""
    
    def test_recaptcha_request_valid(self):
        """Test valid RecaptchaRequest."""
        from src.task2_api.models import RecaptchaRequest
        
        request = RecaptchaRequest(
            sitekey="test-key",
            pageurl="https://example.com"
        )
        assert request.sitekey == "test-key"
        assert request.pageurl == "https://example.com"
        assert request.proxy is None
    
    def test_recaptcha_request_with_proxy(self):
        """Test RecaptchaRequest with proxy."""
        from src.task2_api.models import RecaptchaRequest
        
        request = RecaptchaRequest(
            sitekey="test-key",
            pageurl="https://example.com",
            proxy="http://proxy.com:8080"
        )
        assert request.proxy == "http://proxy.com:8080"
    
    def test_task_status_enum(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PROCESSING == "processing"
        assert TaskStatus.READY == "ready"
        assert TaskStatus.ERROR == "error"


@pytest.mark.asyncio
class TestDatabase:
    """Test database operations."""
    
    async def test_create_task(self):
        """Test creating a task in database."""
        from src.task2_api.database import Database
        from src.task2_api.models import TaskStatus
        
        db = Database(":memory:")  # Use in-memory database
        await db.initialize()
        
        success = await db.create_task(
            task_id="test-123",
            sitekey="test-key",
            pageurl="https://example.com",
            proxy=None,
            status=TaskStatus.PROCESSING
        )
        
        assert success is True
        
        # Verify task was created
        task = await db.get_task("test-123")
        assert task is not None
        assert task["task_id"] == "test-123"
        assert task["status"] == TaskStatus.PROCESSING.value
        
        await db.close()
    
    async def test_update_task(self):
        """Test updating task status."""
        from src.task2_api.database import Database
        from src.task2_api.models import TaskStatus
        
        db = Database(":memory:")
        await db.initialize()
        
        # Create task
        await db.create_task(
            task_id="test-456",
            sitekey="test-key",
            pageurl="https://example.com",
            proxy=None,
            status=TaskStatus.PROCESSING
        )
        
        # Update task
        await db.update_task(
            task_id="test-456",
            status=TaskStatus.READY,
            token="test-token",
            solve_time=10.5
        )
        
        # Verify update
        task = await db.get_task("test-456")
        assert task["status"] == TaskStatus.READY.value
        assert task["token"] == "test-token"
        assert task["solve_time"] == 10.5
        
        await db.close()
    
    async def test_get_statistics(self):
        """Test getting database statistics."""
        from src.task2_api.database import Database
        from src.task2_api.models import TaskStatus
        
        db = Database(":memory:")
        await db.initialize()
        
        # Create some tasks
        await db.create_task("task-1", "key", "url", None, TaskStatus.READY)
        await db.update_task("task-1", TaskStatus.READY, "token", 10.0)
        
        await db.create_task("task-2", "key", "url", None, TaskStatus.PROCESSING)
        
        await db.create_task("task-3", "key", "url", None, TaskStatus.ERROR)
        await db.update_task("task-3", TaskStatus.ERROR, error="Test error")
        
        # Get statistics
        stats = await db.get_statistics()
        assert stats["total_tasks"] == 3
        assert stats["by_status"][TaskStatus.READY.value] == 1
        assert stats["by_status"][TaskStatus.PROCESSING.value] == 1
        assert stats["by_status"][TaskStatus.ERROR.value] == 1
        
        await db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
