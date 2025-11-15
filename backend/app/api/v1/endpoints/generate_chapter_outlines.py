"""
Chapter Outline Generation Endpoint

This endpoint generates a structured chapter outline from a story outline using AI.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, UTC

from app.services.llm_inference import get_llm
from app.services.context_builder import ContextBuilder
from app.models.chapter_models import ChapterOutlineRequest, OutlineItem, ChapterOutlineResponse
# Legacy import removed in B4 - CharacterContext class removed
# from app.models.generation_models import CharacterContext
from app.api.v1.endpoints.shared_utils import parse_json_array_response

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate-chapter-outlines", response_model=ChapterOutlineResponse)
async def generate_chapter_outlines(request: ChapterOutlineRequest):
    """
    Generate a structured chapter outline from a story outline.
    
    This endpoint analyzes the provided story outline and generates a detailed
    chapter-by-chapter breakdown that can be used in the chapter development phase.
    """
    logger.info("Starting chapter outline generation")
    
    if not request.request_context.story_outline.content.strip():
        raise HTTPException(status_code=400, detail="Story outline cannot be empty")
    
    try:
        
        # Initialize LLM service
        llm = get_llm()
        if not llm:
            raise HTTPException(
                status_code=503,
                detail="LLM not initialized. Start server with --model-path")
        
        # Prepare the base system prompt
        system_prompt = """You are an expert story structure analyst and chapter outline generator.
Your task is to analyze a story outline and create a detailed chapter-by-chapter breakdown.

Guidelines:
1. Create 8-15 chapters based on the story outline complexity
2. Each chapter should have a clear purpose and advance the plot
3. Maintain proper story pacing and structure
4. Include key plot points, character development, and conflicts
5. Each chapter title should be engaging and descriptive
6. Generate 3-5 specific key plot items for each chapter that advance the story
7. Each plot item should be a concrete action, event, or revelation
8. Identify which characters are involved in each chapter

IMPORTANT: Format your response as a JSON array where each chapter is an object with these exact fields:
{
  "title": "Chapter title (without 'Chapter X:' prefix)",
  "description": "Brief 2-4 sentence summary of the chapter",
  "key_plot_items": ["Specific plot item 1", "Specific plot item 2", "Specific plot item 3"],
  "involved_characters": ["character1", "character2", ...]
}

Example format:
[
  {
    "title": "The Mysterious Arrival",
    "description": "A strange letter arrives that changes the protagonist's life forever.",
    "key_plot_items": [
      "Protagonist receives an anonymous letter with cryptic instructions",
      "Letter mentions a family secret that was thought buried",
      "Protagonist discovers the letter is written in their deceased father's handwriting",
      "A decision must be made whether to follow the letter's directions"
    ],
    "involved_characters": ["John", "Mary"]
  },
  {
    "title": "Secrets Revealed",
    "description": "Hidden family truths come to light as the protagonist investigates.",
    "key_plot_items": [
      "Protagonist confronts their mother about the letter",
      "Mother reveals the family has been hiding from dangerous people",
      "Old family photographs reveal a connection to a missing person case",
      "Detective Smith arrives asking questions about the father's past"
    ],
    "involved_characters": ["John", "Sarah", "Detective Smith"]
  }
]

Respond ONLY with the JSON array, no additional text."""
        agent_prompt = f"""Please analyze the STORY_OUTLINE and create a detailed chapter breakdown:

Create a chapter-by-chapter outline that breaks down this story into well-structured chapters. Each chapter should advance the plot and contribute to the overall narrative arc. Consider the characters listed above and identify which characters are involved in each chapter."""

        context_builder = ContextBuilder(request_context=request.request_context)
        context_builder.add_system_prompt(system_prompt)
        context_builder.add_worldbuilding()
        context_builder.add_characters()
        context_builder.add_story_outline()
        context_builder.add_agent_instruction(agent_prompt)
        
        # Generate the chapter outline
        response = llm.chat_completion(
            messages=context_builder.build_messages(),
            max_tokens=2000,
            temperature=0.7
        )
        
        # Parse the response into structured outline items
        outline_items = _parse_chapter_outline_response(response)
        if not outline_items:
            raise Exeption('Failed to parse JSON response from LLM')
        
        logger.info(f"Successfully generated {len(outline_items)} chapter outline items")
        
        return ChapterOutlineResponse(
            outline_items=outline_items,
            context_metadata={
                "generation_timestamp": datetime.now(UTC).isoformat(),
                "generated_chapters": len(outline_items)
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating chapter outline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate chapter outline: {str(e)}")

def _parse_chapter_outline_response(response: str) -> List[OutlineItem]:
    """
    Parse the LLM response into structured outline items using shared utilities.
    
    This function uses the existing JSON parsing utilities and falls back to
    text parsing if needed.
    """
    outline_items = []
    
    # Try to parse as JSON array using shared utility
    chapters_data = parse_json_array_response(response)
    
    if chapters_data and isinstance(chapters_data, list):
        for i, chapter_data in enumerate(chapters_data):
            if isinstance(chapter_data, dict):
                # Extract key plot items, fallback to description if not provided
                key_plot_items = chapter_data.get("key_plot_items", [])
                description = chapter_data.get("description", "")
                
                # If no key plot items provided, try to create them from description
                if not key_plot_items and description:
                    key_plot_items = [description]
                
                outline_item = OutlineItem(
                    id=f"chapter-{i+1}",
                    title=chapter_data.get("title", f"Chapter {i+1}"),
                    description=description,
                    key_plot_items=key_plot_items,
                    order=i+1,
                    status="draft",
                    involved_characters=chapter_data.get("involved_characters", []),
                    metadata={
                        "created": datetime.now(UTC).isoformat(),
                        "lastModified": datetime.now(UTC).isoformat()
                    }
                )
                outline_items.append(outline_item)
        
        if outline_items:
            logger.info(f"Successfully parsed {len(outline_items)} chapters from JSON response")
            return outline_items
    
    logger.error("Failed to parse JSON response. Falling back to text parsing.")
    
    return None