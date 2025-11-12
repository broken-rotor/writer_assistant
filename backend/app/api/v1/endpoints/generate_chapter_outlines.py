"""
Chapter Outline Generation Endpoint

This endpoint generates a structured chapter outline from a story outline using AI.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, UTC

from app.services.llm_inference import get_llm
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
    
    if not request.request_context.story_outline.summary.strip():
        raise HTTPException(status_code=400, detail="Story outline cannot be empty")
    
    try:
        
        # Initialize LLM service
        llm = get_llm()
        if not llm:
            raise HTTPException(
                status_code=503,
                detail="LLM not initialized. Start server with --model-path")
        
        # Prepare the base system prompt
        base_system_prompt = """You are an expert story structure analyst and chapter outline generator. Your task is to analyze a story outline and create a detailed chapter-by-chapter breakdown.

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
  "description": "Brief 1-2 sentence summary of the chapter",
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

        # Apply custom system prompts if provided
        system_prompt = base_system_prompt
        if request.request_context.configuration.system_prompts:
            if request.request_context.configuration.system_prompts.main_prefix:
                system_prompt = f"{request.request_context.configuration.system_prompts.main_prefix}\n\n{system_prompt}"
            if request.request_context.configuration.system_prompts.main_suffix:
                system_prompt = f"{system_prompt}\n\n{request.request_context.configuration.system_prompts.main_suffix}"

        # Extract character information from RequestContext
        characters_info = ""
        if request.request_context.characters:
            characters_list = []
            for char_details in request.request_context.characters:
                char_info = f"- {char_details.name}"
                if char_details.basic_bio:
                    char_info += f": {char_details.basic_bio}"
                # Note: personality and goals fields don't exist in CharacterDetails model
                characters_list.append(char_info)
            characters_info = f"""

CHARACTERS:
{chr(10).join(characters_list)}"""

        # Extract additional story context from RequestContext
        story_context_info = ""
        if request.request_context.context_metadata.story_title:
            story_context_info += f"\nSTORY TITLE: {request.request_context.context_metadata.story_title}"
        if request.request_context.worldbuilding.content:
            story_context_info += f"\nWORLDBUILDING: {request.request_context.worldbuilding.content}"

        user_prompt = f"""Please analyze this story outline and create a detailed chapter breakdown:

STORY OUTLINE:
{request.request_context.story_outline.summary}{story_context_info}{characters_info}

Create a chapter-by-chapter outline that breaks down this story into well-structured chapters. Each chapter should advance the plot and contribute to the overall narrative arc. Consider the characters listed above and identify which characters are involved in each chapter."""

        # Generate the chapter outline
        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()}
        ]
        
        response = llm.chat_completion(
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )
        
        # Parse the response into structured outline items
        outline_items = _parse_chapter_outline_response(response)
        
        # Generate a summary
        summary = f"Generated {len(outline_items)} chapters from story outline"
        
        logger.info(f"Successfully generated {len(outline_items)} chapter outline items")
        
        return ChapterOutlineResponse(
            outline_items=outline_items,
            summary=summary,
            context_metadata={
                "generation_timestamp": datetime.now(UTC).isoformat(),
                "source_outline_length": len(request.request_context.story_outline.summary),
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
                    type="chapter",
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
    
    logger.warning("Failed to parse JSON response. Falling back to text parsing.")
    
    # Fallback to text parsing logic
    outline_items = _parse_text_response(response)
    
    # If still no chapters were parsed, create a fallback structure
    if not outline_items:
        outline_items = _create_fallback_chapters(response)
    
    return outline_items

def _parse_text_response(response: str) -> List[OutlineItem]:
    """
    Fallback text parsing for non-JSON responses.
    """
    outline_items = []
    
    # Split response into potential chapters
    lines = response.strip().split('\n')
    current_chapter = None
    chapter_counter = 1
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for chapter headers (various formats)
        if any(indicator in line.lower() for indicator in ['chapter', 'ch.', 'part']):
            # Extract chapter title
            title = line
            # Clean up common prefixes
            for prefix in ['Chapter', 'Ch.', 'Part', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.', '11.', '12.', '13.', '14.', '15.']:
                if title.startswith(prefix):
                    title = title[len(prefix):].strip()
                    if title.startswith(':') or title.startswith('-'):
                        title = title[1:].strip()
                    break
            
            if current_chapter:
                # Save previous chapter
                outline_items.append(current_chapter)
            
            # Start new chapter
            current_chapter = OutlineItem(
                id=f"chapter-{chapter_counter}",
                type="chapter",
                title=title or f"Chapter {chapter_counter}",
                description="",
                key_plot_items=[],  # Empty for text parsing, will be populated from description
                order=chapter_counter - 1,
                status="draft",
                involved_characters=[],  # Empty for text parsing
                metadata={
                    "created": datetime.utcnow().isoformat(),
                    "lastModified": datetime.utcnow().isoformat()
                }
            )
            chapter_counter += 1
            
        elif current_chapter and line:
            # Add to current chapter description
            if current_chapter.description:
                current_chapter.description += " " + line
            else:
                current_chapter.description = line
            
            # Also add to key_plot_items for fallback compatibility
            if line not in current_chapter.key_plot_items:
                current_chapter.key_plot_items.append(line)
    
    # Don't forget the last chapter
    if current_chapter:
        outline_items.append(current_chapter)
    
    return outline_items

def _create_fallback_chapters(content: str) -> List[OutlineItem]:
    """
    Create a basic chapter structure when parsing fails.
    """
    # Create 3 basic chapters as fallback
    chapters = [
        ("Beginning", "Introduction and setup of the story"),
        ("Middle", "Development of conflict and rising action"),
        ("End", "Climax and resolution")
    ]
    
    outline_items = []
    for i, (title, description) in enumerate(chapters):
        outline_items.append(OutlineItem(
            id=f"chapter-{i+1}",
            type="chapter",
            title=title,
            description=description,
            key_plot_items=[description],  # Use description as single plot item for fallback
            order=i,
            status="draft",
            involved_characters=[],  # Empty for fallback chapters
            metadata={
                "created": datetime.utcnow().isoformat(),
                "lastModified": datetime.utcnow().isoformat()
            }
        ))
    
    return outline_items
