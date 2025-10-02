"""
Tests for FastAPI web server endpoints.

Tests the RESTful API for solving puzzles via HTTP.
"""

import pytest
from fastapi.testclient import TestClient

from web_server import app

# Create test client
client = TestClient(app)


class TestHealthEndpoint:
    """Tests for /api/health endpoint."""

    def test_health_check_success(self):
        """Test that health check returns 200 OK."""
        response = client.get("/api/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["solver_ready"] is True
        assert "version" in data


class TestSolveEndpoint:
    """Tests for /api/solve endpoint."""

    def test_solve_valid_puzzle(self):
        """Test solving a valid puzzle returns results."""
        response = client.post("/api/solve", json={
            "center_letter": "n",
            "other_letters": "acuotp"
        })

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        assert "puzzle" in data
        assert "results" in data
        assert "stats" in data

        # Verify puzzle info
        assert data["puzzle"]["center"] == "n"
        assert len(data["puzzle"]["letters"]) == 7

        # Verify results
        assert len(data["results"]) > 0
        first_word = data["results"][0]
        assert "word" in first_word
        assert "confidence" in first_word
        assert "is_pangram" in first_word
        assert "length" in first_word

        # Verify stats
        stats = data["stats"]
        assert stats["total_found"] > 0
        assert stats["remaining"] > 0
        assert stats["solve_time"] > 0

    def test_solve_with_exclude_words(self):
        """Test excluding known words works correctly."""
        # First solve without exclusions
        response1 = client.post("/api/solve", json={
            "center_letter": "n",
            "other_letters": "acuotp"
        })
        total_without_exclude = len(response1.json()["results"])

        # Then solve with exclusions
        response2 = client.post("/api/solve", json={
            "center_letter": "n",
            "other_letters": "acuotp",
            "exclude_words": ["count", "upon"]
        })

        assert response2.status_code == 200
        data = response2.json()

        # Should have fewer results
        assert len(data["results"]) < total_without_exclude

        # Stats should reflect exclusions
        assert data["stats"]["excluded_count"] >= 1  # At least one valid word excluded
        assert len(data["excluded_words"]) >= 1

        # Excluded words should not be in results
        result_words = [r["word"] for r in data["results"]]
        assert "count" not in result_words
        assert "upon" not in result_words

    def test_solve_invalid_center_letter(self):
        """Test that invalid center letter returns 422."""
        response = client.post("/api/solve", json={
            "center_letter": "nn",  # Too long
            "other_letters": "acuotp"
        })

        assert response.status_code == 422  # Pydantic validation error

    def test_solve_invalid_other_letters(self):
        """Test that invalid other_letters returns 422."""
        response = client.post("/api/solve", json={
            "center_letter": "n",
            "other_letters": "abc"  # Too short
        })

        assert response.status_code == 422

    def test_solve_non_alphabetic_input(self):
        """Test that non-alphabetic input returns 422."""
        response = client.post("/api/solve", json={
            "center_letter": "1",
            "other_letters": "acuotp"
        })

        assert response.status_code == 422

    def test_solve_missing_required_fields(self):
        """Test that missing required fields returns 422."""
        response = client.post("/api/solve", json={
            "center_letter": "n"
            # Missing other_letters
        })

        assert response.status_code == 422

    def test_solve_empty_exclude_list(self):
        """Test that empty exclude list works."""
        response = client.post("/api/solve", json={
            "center_letter": "n",
            "other_letters": "acuotp",
            "exclude_words": []
        })

        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["excluded_count"] == 0

    def test_solve_invalid_exclude_words(self):
        """Test that invalid excluded words are ignored gracefully."""
        response = client.post("/api/solve", json={
            "center_letter": "n",
            "other_letters": "acuotp",
            "exclude_words": ["invalidword123", "notreal", "zzzzz"]
        })

        # Should succeed (just ignore invalid words)
        assert response.status_code == 200
        data = response.json()
        # No valid words excluded
        assert data["stats"]["excluded_count"] == 0

    def test_solve_case_insensitive(self):
        """Test that input is case-insensitive."""
        response1 = client.post("/api/solve", json={
            "center_letter": "N",
            "other_letters": "ACUOTP"
        })

        response2 = client.post("/api/solve", json={
            "center_letter": "n",
            "other_letters": "acuotp"
        })

        # Should return same results
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert len(response1.json()["results"]) == len(response2.json()["results"])


class TestCORS:
    """Tests for CORS headers."""

    def test_cors_headers_present(self):
        """Test that CORS headers are present in response."""
        # CORS headers appear when Origin header is present (cross-origin request)
        response = client.post("/api/solve",
            json={
                "center_letter": "n",
                "other_letters": "acuotp"
            },
            headers={"Origin": "http://localhost:3000"}
        )

        # Should allow CORS
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "*"

    def test_cors_methods_allowed(self):
        """Test that correct HTTP methods are allowed."""
        # Check via actual GET request with Origin header
        response = client.get("/api/health",
            headers={"Origin": "http://localhost:3000"}
        )

        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_not_found(self):
        """Test that non-existent endpoints return 404."""
        response = client.get("/api/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_method_not_allowed(self):
        """Test that GET on POST-only endpoint returns error."""
        response = client.get("/api/solve")

        # With static file serving, may return 404 or 405
        assert response.status_code in [404, 405]


class TestAPIDocumentation:
    """Tests for auto-generated API docs."""

    def test_openapi_json_available(self):
        """Test that OpenAPI JSON schema is available."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "/api/solve" in data["paths"]

    def test_swagger_docs_available(self):
        """Test that Swagger UI is available."""
        response = client.get("/api/docs")

        assert response.status_code == 200
        # Swagger UI returns HTML
        assert "text/html" in response.headers["content-type"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
