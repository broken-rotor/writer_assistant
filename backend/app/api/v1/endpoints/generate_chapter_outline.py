"""
Chapter Outline Generation Endpoint

This endpoint generates a structured chapter outline from a story outline using AI.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.services.llm_inference import get_llm

logger = logging.getLogger(__name__)

router = APIRouter()

class ChapterOutlineRequest(BaseModel):
    """Request model for chapter outline generation"""
    story_outline: str = Field(..., description="The story outline content")
    story_context: Dict[str, Any] = Field(default_factory=dict, description="Additional story context")
    generation_preferences: Dict[str, Any] = Field(default_factory=dict, description="Generation preferences")

class OutlineItem(BaseModel):
    """Generated outline item"""
    id: str
    type: str = "chapter"
    title: str
    description: str
    order: int
    status: str = "draft"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChapterOutlineResponse(BaseModel):
    """Response model for chapter outline generation"""
    outline_items: List[OutlineItem]
    summary: str
    context_metadata: Dict[str, Any] = Field(default_factory=dict)

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

Format your response as a structured list where each chapter includes:
- A compelling chapter title
- A detailed description of what happens in the chapter
- The chapter's role in the overall story arc"""

        user_prompt = f"""Please analyze this story outline and create a detailed chapter breakdown:

STORY OUTLINE:
{request.story_outline}

Create a chapter-by-chapter outline that breaks down this story into well-structured chapters. Each chapter should advance the plot and contribute to the overall narrative arc."""

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
    Parse the LLM response into structured outline items.
    
    This function attempts to extract chapter information from the AI response
    and structure it into OutlineItem objects.
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
    
    # If no chapters were parsed, create a fallback structure
    if not outline_items:
        # Create basic chapters from the outline
        outline_items = _create_fallback_chapters(response)
    
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
            metadata={
                "created": datetime.utcnow().isoformat(),
                "lastModified": datetime.utcnow().isoformat()
            }
        ))
    
    return outline_items
