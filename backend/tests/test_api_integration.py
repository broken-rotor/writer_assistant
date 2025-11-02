"""
Integration tests across multiple endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from tests.test_generate_chapter import extract_final_result_from_streaming_response


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
        char_data = extract_final_result_from_streaming_response(char_response)

        # Get rater feedback
        rater_response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        assert rater_response.status_code == 200

        # Generate chapter with feedback
        chapter_response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        chapter_data = extract_final_result_from_streaming_response(chapter_response)

    def test_chapter_generation_to_editor_review(
        self,
        client,
        sample_generate_chapter_request,
        sample_editor_review_request
    ):
        """Test workflow: generate chapter -> editor review"""
        # Generate chapter
        chapter_response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        chapter_data = extract_final_result_from_streaming_response(chapter_response)
        chapter_text = chapter_data["chapterText"]

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
        chapter_data = extract_final_result_from_streaming_response(chapter_response)
        chapter_text = chapter_data["chapterText"]

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
