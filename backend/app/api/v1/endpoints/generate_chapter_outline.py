"""
Chapter Outline Generation Endpoint

This endpoint generates a structured chapter outline from a story outline using AI.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.services.llm_inference import get_llm
from app.models.chapter_models import ChapterOutlineRequest, OutlineItem, ChapterOutlineResponse
from app.models.generation_models import CharacterContext
from app.api.v1.endpoints.shared_utils import parse_json_array_response

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate-chapter-outline", response_model=ChapterOutlineResponse)
async def generate_chapter_outline(request: ChapterOutlineRequest):
    """
    Generate a structured chapter outline from a story outline.
    
    This endpoint analyzes the provided story outline and generates a detailed
    chapter-by-chapter breakdown that can be used in the chapter development phase.
    """
    try:
        logger.info("Starting chapter outline generation")
        
        if not request.story_outline.strip():
            raise HTTPException(status_code=400, detail="Story outline cannot be empty")
        
        # Initialize LLM service
        llm = get_llm()
        if not llm:
            raise HTTPException(
                status_code=503,
                detail="LLM not initialized. Start server with --model-path")
        
        # Prepare the generation prompt
        system_prompt = """You are an expert story structure analyst and chapter outline generator. Your task is to analyze a story outline and create a detailed chapter-by-chapter breakdown.

Guidelines:
1. Create 8-15 chapters based on the story outline complexity
2. Each chapter should have a clear purpose and advance the plot
3. Maintain proper story pacing and structure
4. Include key plot points, character development, and conflicts
5. Each chapter title should be engaging and descriptive
6. Each chapter description should be 2-3 sentences explaining what happens
7. Identify which characters are involved in each chapter

IMPORTANT: Format your response as a JSON array where each chapter is an object with these exact fields:
{
  "title": "Chapter title (without 'Chapter X:' prefix)",
  "description": "2-3 sentence description of what happens",
  "involved_characters": ["character1", "character2", ...]
}

Example format:
[
  {
    "title": "The Mysterious Arrival",
    "description": "The protagonist discovers a strange letter that changes everything. They must decide whether to follow its cryptic instructions or ignore the warning.",
    "involved_characters": ["John", "Mary"]
  },
  {
    "title": "Secrets Revealed",
    "description": "Hidden truths about the family come to light. The protagonist confronts their past and makes a difficult choice.",
    "involved_characters": ["John", "Sarah", "Detective Smith"]
  }
]

Respond ONLY with the JSON array, no additional text."""

        # Extract character information - prefer CharacterContext, fallback to story_context
        characters_info = ""
        if request.character_contexts:
            # Use CharacterContext objects (preferred approach)
            characters_list = []
            for char_context in request.character_contexts:
                char_info = f"- {char_context.character_name}"
                if char_context.personality_traits:
                    char_info += f": {', '.join(char_context.personality_traits)}"
                if char_context.goals:
                    char_info += f" (Goals: {', '.join(char_context.goals)})"
                characters_list.append(char_info)
            characters_info = f"""

CHARACTERS:
{chr(10).join(characters_list)}"""
        elif request.story_context.get('characters'):
            # Fallback to legacy format for backward compatibility
            characters_list = []
            for char in request.story_context['characters']:
                char_info = f"- {char.get('name', 'Unknown')}: {char.get('basicBio', 'No description')}"
                characters_list.append(char_info)
            characters_info = f"""

CHARACTERS:
{chr(10).join(characters_list)}"""

        # Extract additional story context
        story_context_info = ""
        if request.story_context.get('title'):
            story_context_info += f"\nSTORY TITLE: {request.story_context['title']}"
        if request.story_context.get('worldbuilding'):
            story_context_info += f"\nWORLDBUILDING: {request.story_context['worldbuilding']}"

        user_prompt = f"""Please analyze this story outline and create a detailed chapter breakdown:

STORY OUTLINE:
{request.story_outline}{story_context_info}{characters_info}

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
                "generation_timestamp": datetime.utcnow().isoformat(),
                "source_outline_length": len(request.story_outline),
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
                outline_item = OutlineItem(
                    id=f"chapter-{i+1}",
                    type="chapter",
                    title=chapter_data.get("title", f"Chapter {i+1}"),
                    description=chapter_data.get("description", ""),
                    order=i,
                    status="draft",
                    involved_characters=chapter_data.get("involved_characters", []),
                    metadata={
                        "created": datetime.utcnow().isoformat(),
                        "lastModified": datetime.utcnow().isoformat()
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
            order=i,
            status="draft",
            involved_characters=[],  # Empty for fallback chapters
            metadata={
                "created": datetime.utcnow().isoformat(),
                "lastModified": datetime.utcnow().isoformat()
            }
        ))
    
    return outline_items
