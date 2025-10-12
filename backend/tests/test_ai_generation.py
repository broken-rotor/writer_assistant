"""
Comprehensive tests for AI Generation endpoints.
Tests all endpoints in ai_generation.py with various scenarios.
"""
import pytest
from fastapi.testclient import TestClient


class TestCharacterFeedbackEndpoint:
    """Test character feedback generation endpoint"""

    def test_character_feedback_success(self, client, sample_character_feedback_request):
        """Test successful character feedback generation"""
        response = client.post("/api/v1/character-feedback", json=sample_character_feedback_request)
        assert response.status_code == 200
        data = response.json()
        assert "characterName" in data
        assert "feedback" in data

    def test_character_feedback_response_structure(self, client, sample_character_feedback_request):
        """Test character feedback response has correct structure"""
        response = client.post("/api/v1/character-feedback", json=sample_character_feedback_request)
        data = response.json()

        assert data["characterName"] == "Detective Sarah Chen"
        feedback = data["feedback"]
        assert "actions" in feedback
        assert "dialog" in feedback
        assert "physicalSensations" in feedback
        assert "emotions" in feedback
        assert "internalMonologue" in feedback

    def test_character_feedback_arrays_not_empty(self, client, sample_character_feedback_request):
        """Test character feedback arrays contain data"""
        response = client.post("/api/v1/character-feedback", json=sample_character_feedback_request)
        feedback = response.json()["feedback"]

        assert isinstance(feedback["actions"], list)
        assert len(feedback["actions"]) > 0
        assert isinstance(feedback["dialog"], list)
        assert len(feedback["dialog"]) > 0
        assert isinstance(feedback["physicalSensations"], list)
        assert len(feedback["physicalSensations"]) > 0
        assert isinstance(feedback["emotions"], list)
        assert len(feedback["emotions"]) > 0
        assert isinstance(feedback["internalMonologue"], list)
        assert len(feedback["internalMonologue"]) > 0

    def test_character_feedback_missing_required_fields(self, client):
        """Test character feedback fails without required fields"""
        invalid_request = {
            "systemPrompts": {"mainPrefix": "", "mainSuffix": ""},
            "worldbuilding": "Test world"
        }
        response = client.post("/api/v1/character-feedback", json=invalid_request)
        assert response.status_code == 422  # Validation error

    def test_character_feedback_with_empty_plot_point(self, client, sample_character_feedback_request):
        """Test character feedback works with empty plot point"""
        sample_character_feedback_request["plotPoint"] = ""
        response = client.post("/api/v1/character-feedback", json=sample_character_feedback_request)
        assert response.status_code == 200

    def test_character_feedback_with_previous_chapters(self, client, sample_character_feedback_request):
        """Test character feedback with previous chapters"""
        sample_character_feedback_request["previousChapters"] = [
            {"number": 1, "title": "Chapter 1", "content": "Chapter 1 content"},
            {"number": 2, "title": "Chapter 2", "content": "Chapter 2 content"}
        ]
        response = client.post("/api/v1/character-feedback", json=sample_character_feedback_request)
        assert response.status_code == 200


class TestRaterFeedbackEndpoint:
    """Test rater feedback generation endpoint"""

    def test_rater_feedback_success(self, client, sample_rater_feedback_request):
        """Test successful rater feedback generation"""
        response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        assert response.status_code == 200
        data = response.json()
        assert "raterName" in data
        assert "feedback" in data

    def test_rater_feedback_response_structure(self, client, sample_rater_feedback_request):
        """Test rater feedback response has correct structure"""
        response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        data = response.json()

        feedback = data["feedback"]
        assert "opinion" in feedback
        assert "suggestions" in feedback
        assert isinstance(feedback["opinion"], str)
        assert isinstance(feedback["suggestions"], list)

    def test_rater_feedback_has_suggestions(self, client, sample_rater_feedback_request):
        """Test rater feedback includes suggestions"""
        response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        suggestions = response.json()["feedback"]["suggestions"]

        assert len(suggestions) > 0
        for suggestion in suggestions:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0

    def test_rater_feedback_opinion_not_empty(self, client, sample_rater_feedback_request):
        """Test rater opinion is not empty"""
        response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        opinion = response.json()["feedback"]["opinion"]
        assert len(opinion) > 0

    def test_rater_feedback_missing_rater_prompt(self, client):
        """Test rater feedback fails without rater prompt"""
        invalid_request = {
            "systemPrompts": {"mainPrefix": "", "mainSuffix": ""},
            "worldbuilding": "Test",
            "storySummary": "Test",
            "previousChapters": [],
            "plotPoint": "Test"
        }
        response = client.post("/api/v1/rater-feedback", json=invalid_request)
        assert response.status_code == 422

    def test_rater_feedback_with_incorporated_feedback(self, client, sample_rater_feedback_request):
        """Test rater feedback with incorporated feedback items"""
        sample_rater_feedback_request["incorporatedFeedback"] = [
            {"source": "character", "type": "action", "content": "Test", "incorporated": True}
        ]
        response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        assert response.status_code == 200


class TestGenerateChapterEndpoint:
    """Test chapter generation endpoint"""

    def test_generate_chapter_success(self, client, sample_generate_chapter_request):
        """Test successful chapter generation"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        assert response.status_code == 200
        data = response.json()
        assert "chapterText" in data
        assert "wordCount" in data
        assert "metadata" in data

    def test_generate_chapter_response_structure(self, client, sample_generate_chapter_request):
        """Test chapter generation response structure"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        data = response.json()

        assert isinstance(data["chapterText"], str)
        assert isinstance(data["wordCount"], int)
        assert isinstance(data["metadata"], dict)
        assert data["wordCount"] > 0
        assert len(data["chapterText"]) > 0

    def test_generate_chapter_metadata_contains_info(self, client, sample_generate_chapter_request):
        """Test chapter metadata contains expected information"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        metadata = response.json()["metadata"]

        assert "generatedAt" in metadata
        assert "plotPoint" in metadata
        assert "feedbackItemsIncorporated" in metadata

    def test_generate_chapter_with_empty_plot_point(self, client, sample_generate_chapter_request):
        """Test chapter generation with empty plot point"""
        sample_generate_chapter_request["plotPoint"] = ""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        assert response.status_code == 200
        data = response.json()
        assert len(data["chapterText"]) > 0

    def test_generate_chapter_with_multiple_characters(self, client, sample_generate_chapter_request):
        """Test chapter generation with multiple characters"""
        sample_generate_chapter_request["characters"].append({
            "name": "John Doe",
            "basicBio": "A mysterious stranger",
            "sex": "Male",
            "gender": "Male",
            "sexualPreference": "Heterosexual",
            "age": 40,
            "physicalAppearance": "Tall and imposing",
            "usualClothing": "Dark suits",
            "personality": "Enigmatic",
            "motivations": "Unknown",
            "fears": "Exposure",
            "relationships": "None known"
        })
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        assert response.status_code == 200

    def test_generate_chapter_with_incorporated_feedback(self, client, sample_generate_chapter_request):
        """Test chapter generation with incorporated feedback"""
        sample_generate_chapter_request["incorporatedFeedback"] = [
            {"source": "character1", "type": "action", "content": "Consider this", "incorporated": True},
            {"source": "rater1", "type": "suggestion", "content": "Add more detail", "incorporated": True}
        ]
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        assert response.status_code == 200
        metadata = response.json()["metadata"]
        assert metadata["feedbackItemsIncorporated"] == 2

    def test_generate_chapter_word_count_accuracy(self, client, sample_generate_chapter_request):
        """Test that word count is reasonably accurate"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        data = response.json()

        actual_word_count = len(data["chapterText"].split())
        reported_word_count = data["wordCount"]

        # Word count should be exact
        assert actual_word_count == reported_word_count

    def test_generate_chapter_missing_required_fields(self, client):
        """Test chapter generation fails without required fields"""
        invalid_request = {
            "systemPrompts": {"mainPrefix": "", "mainSuffix": ""}
        }
        response = client.post("/api/v1/generate-chapter", json=invalid_request)
        assert response.status_code == 422


class TestModifyChapterEndpoint:
    """Test chapter modification endpoint"""

    def test_modify_chapter_success(self, client, sample_modify_chapter_request):
        """Test successful chapter modification"""
        response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        assert response.status_code == 200
        data = response.json()
        assert "modifiedChapter" in data
        assert "wordCount" in data
        assert "changesSummary" in data

    def test_modify_chapter_response_structure(self, client, sample_modify_chapter_request):
        """Test modify chapter response structure"""
        response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        data = response.json()

        assert isinstance(data["modifiedChapter"], str)
        assert isinstance(data["wordCount"], int)
        assert isinstance(data["changesSummary"], str)
        assert data["wordCount"] > 0

    def test_modify_chapter_includes_original_content(self, client, sample_modify_chapter_request):
        """Test that modified chapter includes original content"""
        original_text = sample_modify_chapter_request["currentChapter"]
        response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        modified_text = response.json()["modifiedChapter"]

        # Original text should be included in the modified version
        assert original_text in modified_text

    def test_modify_chapter_changes_summary_mentions_request(self, client, sample_modify_chapter_request):
        """Test that changes summary mentions the user request"""
        user_request = sample_modify_chapter_request["userRequest"]
        response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        changes_summary = response.json()["changesSummary"]

        # Summary should reference the user's request
        assert "user request" in changes_summary.lower()

    def test_modify_chapter_with_long_user_request(self, client, sample_modify_chapter_request):
        """Test modify chapter with long user request"""
        long_request = "Please modify this chapter by " + "adding more detail " * 50
        sample_modify_chapter_request["userRequest"] = long_request
        response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        assert response.status_code == 200

    def test_modify_chapter_missing_current_chapter(self, client):
        """Test modify chapter fails without current chapter"""
        invalid_request = {
            "systemPrompts": {"mainPrefix": "", "mainSuffix": ""},
            "worldbuilding": "Test",
            "storySummary": "Test",
            "previousChapters": [],
            "userRequest": "Change something"
        }
        response = client.post("/api/v1/modify-chapter", json=invalid_request)
        assert response.status_code == 422


class TestEditorReviewEndpoint:
    """Test editor review endpoint"""

    def test_editor_review_success(self, client, sample_editor_review_request):
        """Test successful editor review"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data

    def test_editor_review_response_structure(self, client, sample_editor_review_request):
        """Test editor review response structure"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        data = response.json()

        assert isinstance(data["suggestions"], list)
        assert len(data["suggestions"]) > 0

    def test_editor_review_suggestion_structure(self, client, sample_editor_review_request):
        """Test individual suggestion structure"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        suggestions = response.json()["suggestions"]

        for suggestion in suggestions:
            assert "issue" in suggestion
            assert "suggestion" in suggestion
            assert "priority" in suggestion
            assert isinstance(suggestion["issue"], str)
            assert isinstance(suggestion["suggestion"], str)
            assert suggestion["priority"] in ["high", "medium", "low"]

    def test_editor_review_has_multiple_priorities(self, client, sample_editor_review_request):
        """Test editor review includes suggestions with different priorities"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        suggestions = response.json()["suggestions"]

        priorities = set(s["priority"] for s in suggestions)
        # Should have at least 2 different priority levels
        assert len(priorities) >= 2

    def test_editor_review_with_characters(self, client, sample_editor_review_request):
        """Test editor review with character information"""
        sample_editor_review_request["characters"] = [
            {
                "name": "Character 1",
                "basicBio": "A test character",
                "sex": "Female",
                "gender": "Female",
                "sexualPreference": "Heterosexual",
                "age": 30,
                "physicalAppearance": "Average",
                "usualClothing": "Casual",
                "personality": "Friendly",
                "motivations": "Success",
                "fears": "Failure",
                "relationships": "None"
            }
        ]
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        assert response.status_code == 200

    def test_editor_review_missing_chapter(self, client):
        """Test editor review fails without chapter to review"""
        invalid_request = {
            "systemPrompts": {"mainPrefix": "", "mainSuffix": ""},
            "worldbuilding": "Test",
            "storySummary": "Test",
            "previousChapters": [],
            "characters": []
        }
        response = client.post("/api/v1/editor-review", json=invalid_request)
        assert response.status_code == 422


class TestFleshOutEndpoint:
    """Test flesh out text expansion endpoint"""

    def test_flesh_out_success(self, client, sample_flesh_out_request):
        """Test successful text expansion"""
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        assert response.status_code == 200
        data = response.json()
        assert "fleshedOutText" in data
        assert "originalText" in data

    def test_flesh_out_response_structure(self, client, sample_flesh_out_request):
        """Test flesh out response structure"""
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        data = response.json()

        assert isinstance(data["fleshedOutText"], str)
        assert isinstance(data["originalText"], str)
        assert len(data["fleshedOutText"]) > len(data["originalText"])

    def test_flesh_out_includes_original_text(self, client, sample_flesh_out_request):
        """Test fleshed out text includes original"""
        original = sample_flesh_out_request["textToFleshOut"]
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        fleshed_out = response.json()["fleshedOutText"]

        assert original in fleshed_out

    def test_flesh_out_returns_original_text(self, client, sample_flesh_out_request):
        """Test that original text is returned unchanged"""
        original = sample_flesh_out_request["textToFleshOut"]
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        returned_original = response.json()["originalText"]

        assert original == returned_original

    def test_flesh_out_with_short_text(self, client, sample_flesh_out_request):
        """Test flesh out with very short text"""
        sample_flesh_out_request["textToFleshOut"] = "The detective arrives."
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        assert response.status_code == 200

    def test_flesh_out_with_long_text(self, client, sample_flesh_out_request):
        """Test flesh out with longer text"""
        long_text = "The investigation begins. " * 20
        sample_flesh_out_request["textToFleshOut"] = long_text
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        assert response.status_code == 200

    def test_flesh_out_with_different_contexts(self, client, sample_flesh_out_request):
        """Test flesh out with different context types"""
        contexts = ["worldbuilding", "plot point", "character development", "scene description"]

        for context in contexts:
            sample_flesh_out_request["context"] = context
            response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
            assert response.status_code == 200

    def test_flesh_out_missing_text_to_flesh_out(self, client):
        """Test flesh out fails without text to expand"""
        invalid_request = {
            "systemPrompts": {"mainPrefix": "", "mainSuffix": ""},
            "worldbuilding": "Test",
            "storySummary": "Test",
            "context": "Test"
        }
        response = client.post("/api/v1/flesh-out", json=invalid_request)
        assert response.status_code == 422


class TestGenerateCharacterDetailsEndpoint:
    """Test character details generation endpoint"""

    def test_generate_character_details_success(self, client, sample_generate_character_request):
        """Test successful character details generation"""
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "sex" in data
        assert "gender" in data
        assert "age" in data

    def test_generate_character_details_response_structure(self, client, sample_generate_character_request):
        """Test character details response has all required fields"""
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        data = response.json()

        required_fields = [
            "name", "sex", "gender", "sexualPreference", "age",
            "physicalAppearance", "usualClothing", "personality",
            "motivations", "fears", "relationships"
        ]

        for field in required_fields:
            assert field in data

    def test_generate_character_details_field_types(self, client, sample_generate_character_request):
        """Test character details field types are correct"""
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        data = response.json()

        assert isinstance(data["name"], str)
        assert isinstance(data["sex"], str)
        assert isinstance(data["gender"], str)
        assert isinstance(data["sexualPreference"], str)
        assert isinstance(data["age"], int)
        assert isinstance(data["physicalAppearance"], str)
        assert isinstance(data["usualClothing"], str)
        assert isinstance(data["personality"], str)
        assert isinstance(data["motivations"], str)
        assert isinstance(data["fears"], str)
        assert isinstance(data["relationships"], str)

    def test_generate_character_details_age_is_positive(self, client, sample_generate_character_request):
        """Test generated character age is positive"""
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        age = response.json()["age"]
        assert age > 0

    def test_generate_character_details_with_existing_characters(self, client, sample_generate_character_request):
        """Test character generation with existing characters"""
        sample_generate_character_request["existingCharacters"] = [
            {"name": "John Doe", "basicBio": "A detective", "relationships": "None"},
            {"name": "Jane Smith", "basicBio": "A journalist", "relationships": "Colleague of John"}
        ]
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        assert response.status_code == 200
        relationships = response.json()["relationships"]
        # Should reference existing characters
        assert len(relationships) > 0

    def test_generate_character_details_without_existing_characters(self, client, sample_generate_character_request):
        """Test character generation without existing characters"""
        sample_generate_character_request["existingCharacters"] = []
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        assert response.status_code == 200

    def test_generate_character_details_fields_not_empty(self, client, sample_generate_character_request):
        """Test that key fields are not empty"""
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        data = response.json()

        # These fields should have meaningful content
        assert len(data["name"]) > 0
        assert len(data["physicalAppearance"]) > 10
        assert len(data["personality"]) > 10
        assert len(data["motivations"]) > 10
        assert len(data["fears"]) > 10

    def test_generate_character_details_missing_basic_bio(self, client):
        """Test character generation fails without basic bio"""
        invalid_request = {
            "systemPrompts": {"mainPrefix": "", "mainSuffix": ""},
            "worldbuilding": "Test",
            "storySummary": "Test",
            "existingCharacters": []
        }
        response = client.post("/api/v1/generate-character-details", json=invalid_request)
        assert response.status_code == 422


class TestAPIIntegration:
    """Integration tests across multiple endpoints"""

    def test_full_workflow_character_to_chapter(
        self,
        client,
        sample_character_feedback_request,
        sample_rater_feedback_request,
        sample_generate_chapter_request
    ):
        """Test workflow: character feedback -> rater feedback -> generate chapter"""
        # Get character feedback
        char_response = client.post("/api/v1/character-feedback", json=sample_character_feedback_request)
        assert char_response.status_code == 200

        # Get rater feedback
        rater_response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        assert rater_response.status_code == 200

        # Generate chapter with feedback
        chapter_response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        assert chapter_response.status_code == 200

    def test_chapter_generation_to_editor_review(
        self,
        client,
        sample_generate_chapter_request,
        sample_editor_review_request
    ):
        """Test workflow: generate chapter -> editor review"""
        # Generate chapter
        chapter_response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        assert chapter_response.status_code == 200
        chapter_text = chapter_response.json()["chapterText"]

        # Get editor review of the chapter
        sample_editor_review_request["chapterToReview"] = chapter_text
        editor_response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        assert editor_response.status_code == 200
        assert len(editor_response.json()["suggestions"]) > 0

    def test_chapter_modification_workflow(
        self,
        client,
        sample_generate_chapter_request,
        sample_modify_chapter_request
    ):
        """Test workflow: generate chapter -> modify chapter"""
        # Generate chapter
        chapter_response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        assert chapter_response.status_code == 200
        chapter_text = chapter_response.json()["chapterText"]

        # Modify the chapter
        sample_modify_chapter_request["currentChapter"] = chapter_text
        modify_response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        assert modify_response.status_code == 200
        assert chapter_text in modify_response.json()["modifiedChapter"]

    def test_flesh_out_to_chapter_workflow(
        self,
        client,
        sample_flesh_out_request,
        sample_generate_chapter_request
    ):
        """Test workflow: flesh out plot point -> generate chapter"""
        # Flesh out a plot point
        flesh_response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        assert flesh_response.status_code == 200
        fleshed_text = flesh_response.json()["fleshedOutText"]

        # Use fleshed out text as plot point for chapter
        sample_generate_chapter_request["plotPoint"] = fleshed_text
        chapter_response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        assert chapter_response.status_code == 200
