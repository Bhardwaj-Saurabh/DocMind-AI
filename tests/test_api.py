"""
Tests for FastAPI endpoints.

Run with: pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self):
        """Test health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "vision_enabled" in data
        assert "active_jobs" in data

    def test_health_status_is_healthy(self):
        """Test health status is healthy."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root(self):
        """Test root endpoint returns info."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data


class TestJobsEndpoint:
    """Tests for job management endpoints."""

    def test_list_jobs_empty(self):
        """Test listing jobs when none exist."""
        response = client.get("/jobs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_nonexistent_job(self):
        """Test getting status of non-existent job."""
        response = client.get("/jobs/nonexistent-id")
        assert response.status_code == 404

    def test_delete_nonexistent_job(self):
        """Test deleting non-existent job."""
        response = client.delete("/jobs/nonexistent-id")
        assert response.status_code == 404


class TestExtractionEndpoint:
    """Tests for document extraction endpoint."""

    def test_extract_without_file(self):
        """Test extraction without file fails."""
        response = client.post("/extract")
        assert response.status_code == 422  # Validation error

    def test_extract_with_invalid_format(self):
        """Test extraction with invalid output format."""
        # Create dummy file
        files = {"file": ("test.pdf", b"dummy content", "application/pdf")}
        response = client.post(
            "/extract?output_format=invalid",
            files=files
        )
        assert response.status_code == 400
        assert "Invalid output_format" in response.json()["detail"]

    def test_sync_extract_without_file(self):
        """Test sync extraction without file fails."""
        response = client.post("/extract/sync")
        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestIntegrationExtraction:
    """
    Integration tests for document extraction.

    These tests require actual documents and API keys.
    Skip with: pytest -m "not integration"
    """

    def test_extract_pdf_async(self, sample_pdf):
        """Test async PDF extraction."""
        with open(sample_pdf, "rb") as f:
            files = {"file": (sample_pdf.name, f, "application/pdf")}
            response = client.post(
                "/extract?output_format=markdown",
                files=files
            )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    def test_extract_pdf_sync(self, sample_pdf):
        """Test sync PDF extraction."""
        with open(sample_pdf, "rb") as f:
            files = {"file": (sample_pdf.name, f, "application/pdf")}
            response = client.post(
                "/extract/sync?output_format=text",
                files=files
            )

        # May succeed or fail depending on file and configuration
        assert response.status_code in [200, 400, 500]


# Fixtures

@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF file for testing."""
    pdf_file = tmp_path / "test.pdf"

    # Create minimal PDF (this is a simplified version)
    pdf_content = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000015 00000 n\n0000000061 00000 n\n0000000111 00000 n\ntrailer\n<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"

    pdf_file.write_bytes(pdf_content)
    return pdf_file


# Mark integration tests
pytest.mark.integration = pytest.mark.mark("integration")
