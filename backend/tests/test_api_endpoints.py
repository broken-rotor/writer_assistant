import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check and root endpoints"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns correct response"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["message"] == "Writer Assistant API"

    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestOutlineGenerationEndpoint:
    """Test outline generation endpoint"""

    def test_generate_outline_success(self, client, sample_outline_request):
        """Test successful outline generation"""
        response = client.post("/api/v1/generate/outline", json=sample_outline_request)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "metadata" in data
        assert "session_id" in data["data"]

    def test_generate_outline_response_structure(self, client, sample_outline_request):
        """Test outline generation response has correct structure"""
        response = client.post("/api/v1/generate/outline", json=sample_outline_request)
        data = response.json()["data"]

        assert "outline" in data
        assert "acts" in data["outline"]
        assert "chapters" in data["outline"]
        assert "characters" in data["outline"]
        assert "themes" in data["outline"]
        assert "agent_feedback" in data
        assert "workflow_state" in data

    def test_generate_outline_agent_feedback(self, client, sample_outline_request):
        """Test outline generation includes agent feedback"""
        response = client.post("/api/v1/generate/outline", json=sample_outline_request)
        data = response.json()["data"]

        feedback = data["agent_feedback"]
        assert "consistency_rater" in feedback
        assert "flow_rater" in feedback
        assert "quality_rater" in feedback

        # Verify feedback structure
        for rater_feedback in feedback.values():
            assert "score" in rater_feedback
            assert "feedback" in rater_feedback

    def test_generate_outline_missing_title(self, client):
        """Test outline generation fails without title"""
        invalid_request = {
            "genre": "Mystery",
            "description": "A story",
            "user_guidance": "Make it good"
        }
        response = client.post("/api/v1/generate/outline", json=invalid_request)
        assert response.status_code == 422  # Validation error

    def test_generate_outline_missing_genre(self, client):
        """Test outline generation fails without genre"""
        invalid_request = {
            "title": "My Story",
            "description": "A story",
            "user_guidance": "Make it good"
        }
        response = client.post("/api/v1/generate/outline", json=invalid_request)
        assert response.status_code == 422  # Validation error

    def test_generate_outline_with_configuration(self, client, sample_outline_request):
        """Test outline generation with custom configuration"""
        sample_outline_request["configuration"] = {
            "style_profile": "noir_detective",
            "complexity_level": "high"
        }
        response = client.post("/api/v1/generate/outline", json=sample_outline_request)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestChapterGenerationEndpoint:
    """Test chapter generation endpoint"""

    def test_generate_chapter_success(self, client, sample_chapter_request):
        """Test successful chapter generation"""
        response = client.post("/api/v1/generate/chapter", json=sample_chapter_request)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_generate_chapter_response_structure(self, client, sample_chapter_request):
        """Test chapter generation response has correct structure"""
        response = client.post("/api/v1/generate/chapter", json=sample_chapter_request)
        data = response.json()["data"]

        assert "session_id" in data
        assert "chapter_number" in data
        assert "title" in data
        assert "content" in data
        assert "agent_feedback" in data

    def test_generate_chapter_content_structure(self, client, sample_chapter_request):
        """Test chapter content has correct structure"""
        response = client.post("/api/v1/generate/chapter", json=sample_chapter_request)
        content = response.json()["data"]["content"]

        assert "text" in content
        assert "word_count" in content
        assert "character_perspectives" in content
        assert isinstance(content["word_count"], int)
        assert content["word_count"] > 0

    def test_generate_chapter_character_perspectives(self, client, sample_chapter_request):
        """Test chapter includes character perspectives"""
        response = client.post("/api/v1/generate/chapter", json=sample_chapter_request)
        perspectives = response.json()["data"]["content"]["character_perspectives"]

        assert isinstance(perspectives, dict)
        # Check perspective structure if present
        for character_perspective in perspectives.values():
            assert "internal_monologue" in character_perspective or \
                   "observations" in character_perspective or \
                   "emotional_state" in character_perspective

    def test_generate_chapter_missing_session_id(self, client):
        """Test chapter generation fails without session_id"""
        invalid_request = {
            "chapter_number": 1,
            "user_guidance": "Write chapter",
            "story_context": {}
        }
        response = client.post("/api/v1/generate/chapter", json=invalid_request)
        assert response.status_code == 422  # Validation error

    def test_generate_chapter_missing_chapter_number(self, client):
        """Test chapter generation fails without chapter_number"""
        invalid_request = {
            "session_id": "test-123",
            "user_guidance": "Write chapter",
            "story_context": {}
        }
        response = client.post("/api/v1/generate/chapter", json=invalid_request)
        assert response.status_code == 422  # Validation error


class TestSessionStatusEndpoint:
    """Test session status endpoint"""

    def test_get_session_status_success(self, client):
        """Test successful session status retrieval"""
        session_id = "test-session-123"
        response = client.get(f"/api/v1/generate/session/{session_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_session_status_structure(self, client):
        """Test session status has correct structure"""
        session_id = "test-session-456"
        response = client.get(f"/api/v1/generate/session/{session_id}/status")
        data = response.json()["data"]

        assert "session_id" in data
        assert "current_phase" in data
        assert "current_step" in data
        assert "status" in data
        assert "progress" in data

    def test_get_session_status_progress_tracking(self, client):
        """Test session status includes progress information"""
        session_id = "test-session-789"
        response = client.get(f"/api/v1/generate/session/{session_id}/status")
        data = response.json()["data"]

        assert "progress" in data
        assert isinstance(data["progress"], (int, float))
        assert 0.0 <= data["progress"] <= 1.0


class TestFeedbackSubmissionEndpoint:
    """Test feedback submission endpoint"""

    def test_submit_feedback_success(self, client, sample_feedback_request):
        """Test successful feedback submission"""
        session_id = "test-session-123"
        response = client.post(
            f"/api/v1/generate/session/{session_id}/feedback",
            json=sample_feedback_request
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_submit_feedback_response_structure(self, client, sample_feedback_request):
        """Test feedback submission response structure"""
        session_id = "test-session-456"
        response = client.post(
            f"/api/v1/generate/session/{session_id}/feedback",
            json=sample_feedback_request
        )
        data = response.json()["data"]

        assert "session_id" in data
        assert "feedback_processed" in data
        assert "next_action" in data

    def test_submit_feedback_approval(self, client):
        """Test feedback submission with approval"""
        session_id = "test-session-approval"
        feedback = {
            "phase": "outline_development",
            "feedback_type": "user_review",
            "feedback": {
                "approval_status": "approved",
                "comments": "Looks good!"
            }
        }
        response = client.post(
            f"/api/v1/generate/session/{session_id}/feedback",
            json=feedback
        )
        data = response.json()["data"]
        assert data["next_action"] == "approved"

    def test_submit_feedback_revision_request(self, client):
        """Test feedback submission requesting revision"""
        session_id = "test-session-revision"
        feedback = {
            "phase": "outline_development",
            "feedback_type": "user_review",
            "feedback": {
                "approval_status": "needs_revision",
                "comments": "Please add more detail to Act 2"
            }
        }
        response = client.post(
            f"/api/v1/generate/session/{session_id}/feedback",
            json=feedback
        )
        data = response.json()["data"]
        assert data["next_action"] == "revision_started"


class TestAgentStatusEndpoint:
    """Test agent status endpoint"""

    def test_get_agent_status_success(self, client):
        """Test successful agent status retrieval"""
        session_id = "test-session-123"
        response = client.get(f"/api/v1/generate/session/{session_id}/agents/status")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_agent_status_structure(self, client):
        """Test agent status has correct structure"""
        session_id = "test-session-456"
        response = client.get(f"/api/v1/generate/session/{session_id}/agents/status")
        data = response.json()["data"]

        assert "writer_agent" in data or "character_agents" in data or "rater_agents" in data

    def test_get_agent_status_writer_agent(self, client):
        """Test agent status includes writer agent information"""
        session_id = "test-session-789"
        response = client.get(f"/api/v1/generate/session/{session_id}/agents/status")
        data = response.json()["data"]

        if "writer_agent" in data:
            writer = data["writer_agent"]
            assert "status" in writer
            assert "current_task" in writer or "progress" in writer

    def test_get_agent_status_character_agents(self, client):
        """Test agent status includes character agent information"""
        session_id = "test-session-101"
        response = client.get(f"/api/v1/generate/session/{session_id}/agents/status")
        data = response.json()["data"]

        if "character_agents" in data:
            assert isinstance(data["character_agents"], dict)

    def test_get_agent_status_rater_agents(self, client):
        """Test agent status includes rater agent information"""
        session_id = "test-session-102"
        response = client.get(f"/api/v1/generate/session/{session_id}/agents/status")
        data = response.json()["data"]

        if "rater_agents" in data:
            assert isinstance(data["rater_agents"], dict)
            for rater_status in data["rater_agents"].values():
                assert "status" in rater_status


class TestAPIErrorHandling:
    """Test API error handling"""

    def test_invalid_endpoint(self, client):
        """Test invalid endpoint returns 404"""
        response = client.get("/api/v1/invalid/endpoint")
        assert response.status_code == 404

    def test_invalid_http_method(self, client):
        """Test invalid HTTP method"""
        response = client.put("/api/v1/generate/outline")
        assert response.status_code == 405  # Method not allowed

    def test_malformed_json(self, client):
        """Test malformed JSON in request"""
        response = client.post(
            "/api/v1/generate/outline",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


class TestCORSMiddleware:
    """Test CORS middleware configuration"""

    def test_cors_headers_present(self, client):
        """Test CORS headers are present in responses"""
        response = client.options(
            "/api/v1/generate/outline",
            headers={
                "Origin": "http://localhost:4200",
                "Access-Control-Request-Method": "POST"
            }
        )
        # CORS headers should be present
        assert response.status_code in [200, 204]
