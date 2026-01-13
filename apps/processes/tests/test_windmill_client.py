"""Tests for Windmill client."""

from unittest.mock import MagicMock, patch

import pytest

from processes.services.windmill_client import (
    WindmillClient,
    WindmillError,
    WindmillJobNotFound,
    windmill_client,
)


class TestWindmillClientInit:
    """Tests for WindmillClient initialization."""

    def test_client_instance_exists(self):
        """Test global client instance is available."""
        assert windmill_client is not None
        assert isinstance(windmill_client, WindmillClient)

    def test_client_lazy_init(self):
        """Test client initializes lazily."""
        client = WindmillClient()
        assert client._client is None

    def test_get_client_creates_instance(self):
        """Test _get_client creates Windmill instance."""
        client = WindmillClient()
        with patch("processes.services.windmill_client.Windmill") as mock_windmill:
            mock_instance = MagicMock()
            mock_windmill.return_value = mock_instance

            result = client._get_client()

            assert result == mock_instance
            mock_windmill.assert_called_once()


class TestWindmillClientRunScriptAsync:
    """Tests for run_script_async method."""

    @pytest.mark.asyncio
    async def test_run_script_async_success(self):
        """Test successful async script execution."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_wm.workspace = "goat"
            mock_response = MagicMock()
            mock_response.text = "job-123-456"
            mock_wm.post.return_value = mock_response
            mock_get_client.return_value = mock_wm

            job_id = await client.run_script_async(
                script_path="f/goat/buffer",
                args={"distance": 100},
            )

            assert job_id == "job-123-456"

    @pytest.mark.asyncio
    async def test_run_script_async_with_schedule(self):
        """Test async script execution with scheduled delay."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_wm.workspace = "goat"
            mock_response = MagicMock()
            mock_response.text = "job-789"
            mock_wm.post.return_value = mock_response
            mock_get_client.return_value = mock_wm

            job_id = await client.run_script_async(
                script_path="f/goat/clip",
                args={"input": "layer-1"},
                scheduled_in_secs=60,
            )

            assert job_id == "job-789"

    @pytest.mark.asyncio
    async def test_run_script_async_error(self):
        """Test error handling in run_script_async."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_wm.workspace = "goat"
            mock_wm.post.side_effect = Exception("Connection failed")
            mock_get_client.return_value = mock_wm

            with pytest.raises(WindmillError) as exc_info:
                await client.run_script_async(
                    script_path="f/goat/buffer",
                    args={},
                )

            assert "Failed to submit job" in str(exc_info.value)


class TestWindmillClientGetJobStatus:
    """Tests for get_job_status method."""

    @pytest.mark.asyncio
    async def test_get_job_status_success(self):
        """Test getting job status."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_wm.get_job.return_value = {
                "id": "job-123",
                "running": True,
                "success": None,
            }
            mock_get_client.return_value = mock_wm

            status = await client.get_job_status("job-123")

            assert status["id"] == "job-123"
            assert status["running"] is True

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self):
        """Test getting status for nonexistent job."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_wm.get_job.side_effect = Exception("Job not found: 404")
            mock_get_client.return_value = mock_wm

            with pytest.raises(WindmillJobNotFound):
                await client.get_job_status("nonexistent-job")


class TestWindmillClientGetJobStatusSimple:
    """Tests for get_job_status_simple method."""

    @pytest.mark.asyncio
    async def test_get_job_status_simple_running(self):
        """Test getting simple status for running job."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_wm.get_job_status.return_value = "RUNNING"
            mock_get_client.return_value = mock_wm

            status = await client.get_job_status_simple("job-123")

            assert status == "RUNNING"

    @pytest.mark.asyncio
    async def test_get_job_status_simple_completed(self):
        """Test getting simple status for completed job."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_wm.get_job_status.return_value = "COMPLETED"
            mock_get_client.return_value = mock_wm

            status = await client.get_job_status_simple("job-456")

            assert status == "COMPLETED"


class TestWindmillClientGetJobResult:
    """Tests for get_job_result method."""

    @pytest.mark.asyncio
    async def test_get_job_result_success(self):
        """Test getting job result."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_wm.get_result.return_value = {"output": "result-data"}
            mock_get_client.return_value = mock_wm

            result = await client.get_job_result("job-123")

            assert result["output"] == "result-data"

    @pytest.mark.asyncio
    async def test_get_job_result_not_found(self):
        """Test getting result for nonexistent job."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_wm.get_result.side_effect = Exception("not found")
            mock_get_client.return_value = mock_wm

            with pytest.raises(WindmillJobNotFound):
                await client.get_job_result("nonexistent")


class TestWindmillClientCancelJob:
    """Tests for cancel_job method."""

    @pytest.mark.asyncio
    async def test_cancel_job_success(self):
        """Test cancelling a job."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_wm.cancel_job.return_value = "Job cancelled"
            mock_get_client.return_value = mock_wm

            response = await client.cancel_job("job-123", "User requested")

            assert response == "Job cancelled"

    @pytest.mark.asyncio
    async def test_cancel_job_not_found(self):
        """Test cancelling nonexistent job."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_wm.cancel_job.side_effect = Exception("404 not found")
            mock_get_client.return_value = mock_wm

            with pytest.raises(WindmillJobNotFound):
                await client.cancel_job("nonexistent")


class TestWindmillClientListJobs:
    """Tests for list_jobs method."""

    @pytest.mark.asyncio
    async def test_list_jobs_all(self):
        """Test listing all jobs."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {"id": "job-1", "running": True},
                {"id": "job-2", "running": False},
            ]
            mock_wm.get.return_value = mock_response
            mock_get_client.return_value = mock_wm

            jobs = await client.list_jobs()

            assert len(jobs) == 2
            assert jobs[0]["id"] == "job-1"

    @pytest.mark.asyncio
    async def test_list_jobs_filtered(self):
        """Test listing jobs with filters."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = [{"id": "job-1"}]
            mock_wm.get.return_value = mock_response
            mock_get_client.return_value = mock_wm

            jobs = await client.list_jobs(
                running=True,
                script_path="f/goat/buffer",
                limit=10,
            )

            assert len(jobs) == 1


class TestWindmillClientRunScriptSync:
    """Tests for run_script_sync method."""

    @pytest.mark.asyncio
    async def test_run_script_sync_success(self):
        """Test synchronous script execution."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_wm.run_script_by_path.return_value = {"result": "done"}
            mock_get_client.return_value = mock_wm

            result = await client.run_script_sync(
                script_path="f/goat/simple",
                args={"input": "data"},
            )

            assert result["result"] == "done"

    @pytest.mark.asyncio
    async def test_run_script_sync_with_timeout(self):
        """Test synchronous script execution with timeout."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_wm.run_script_by_path.return_value = {"status": "ok"}
            mock_get_client.return_value = mock_wm

            result = await client.run_script_sync(
                script_path="f/goat/long-running",
                args={},
                timeout=300.0,
            )

            assert result["status"] == "ok"


class TestWindmillClientWaitForJob:
    """Tests for wait_for_job method."""

    @pytest.mark.asyncio
    async def test_wait_for_job_success(self):
        """Test waiting for job completion."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_wm.wait_job.return_value = {"completed": True}
            mock_get_client.return_value = mock_wm

            result = await client.wait_for_job("job-123")

            assert result["completed"] is True

    @pytest.mark.asyncio
    async def test_wait_for_job_with_timeout(self):
        """Test waiting with timeout."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_wm.wait_job.return_value = {"done": True}
            mock_get_client.return_value = mock_wm

            result = await client.wait_for_job("job-456", timeout=60.0)

            assert result["done"] is True


class TestWindmillClientClose:
    """Tests for close method."""

    @pytest.mark.asyncio
    async def test_close_with_client(self):
        """Test closing client with active connection."""
        client = WindmillClient()
        mock_wm = MagicMock()
        mock_http_client = MagicMock()
        mock_wm.client = mock_http_client
        client._client = mock_wm

        await client.close()

        mock_http_client.close.assert_called_once()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_without_client(self):
        """Test closing client without active connection."""
        client = WindmillClient()
        client._client = None

        # Should not raise
        await client.close()

        assert client._client is None


class TestWindmillClientWhoami:
    """Tests for whoami method."""

    @pytest.mark.asyncio
    async def test_whoami_success(self):
        """Test getting current user info."""
        client = WindmillClient()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_wm = MagicMock()
            mock_wm.whoami.return_value = {
                "email": "test@example.com",
                "username": "testuser",
            }
            mock_get_client.return_value = mock_wm

            user = await client.whoami()

            assert user["email"] == "test@example.com"
            assert user["username"] == "testuser"
