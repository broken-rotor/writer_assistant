"""
RequestContext models for the Writer Assistant backend API.

This module defines a comprehensive RequestContext object that encapsulates
all story state information from the frontend, providing a complete and
self-contained representation for backend processing.

The RequestContext is designed to replace the current StructuredContextContainer
with a richer, more complete data structure that preserves all frontend
information without transformation loss.

Key Features:
- Complete story state preservation
- Rich character and chapter details
- Comprehensive feedback integration
- Conversation history tracking
- Hierarchical outline structure
- Extensive metadata for optimization

Author: Codegen Bot
Issue: WRI-138 - New RequestContext for the backend API
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class SystemPrompts(BaseModel):
    """Agent-specific system prompts configuration."""
    main_prefix: str = Field(description="Main system prompt prefix")
    main_suffix: str = Field(description="Main system prompt suffix")
    assistant_prompt: str = Field(description="Assistant agent prompt")
    editor_prompt: str = Field(description="Editor agent prompt")


class RaterConfig(BaseModel):
    """Configuration for rater agents."""
    id: str = Field(description="Unique rater identifier")
    name: str = Field(description="Rater display name")
    system_prompt: str = Field(description="Rater-specific system prompt")
    enabled: bool = Field(description="Whether this rater is active")


class StoryConfiguration(BaseModel):
    """System prompts and agent configuration."""
    system_prompts: SystemPrompts = Field(description="Agent-specific prompts")
    raters: List[RaterConfig] = Field(
        default_factory=list,
        description="List of configured rater agents"
    )


class ChatMessage(BaseModel):
    """Individual message in a conversation thread."""
    id: str = Field(description="Unique message identifier")
    type: Literal["user", "assistant", "system"] = Field(
        description="Type of message sender"
    )
    content: str = Field(description="Message content")
    timestamp: datetime = Field(description="When the message was created")
    author: Optional[str] = Field(
        None,
        description="Author identifier for system messages"
    )


class WorldbuildingInfo(BaseModel):
    """Complete worldbuilding context information."""
    content: str = Field(description="Main worldbuilding content")
    chat_history: List[ChatMessage] = Field(
        default_factory=list,
        description="Worldbuilding conversation history"
    )


class CharacterDetails(BaseModel):
    """Complete character information and context."""
    id: str = Field(description="Unique character identifier")
    name: str = Field(description="Character name")
    basic_bio: str = Field(description="Basic character biography")
    
    # Demographics
    sex: str = Field(default="", description="Character sex")
    gender: str = Field(default="", description="Character gender identity")
    sexual_preference: str = Field(default="", description="Character sexual preference")
    age: int = Field(default=0, description="Character age")
    
    # Appearance
    physical_appearance: str = Field(default="", description="Physical appearance description")
    usual_clothing: str = Field(default="", description="Typical clothing style")
    
    # Psychology
    personality: str = Field(default="", description="Personality traits and characteristics")
    motivations: str = Field(default="", description="Character motivations and drives")
    fears: str = Field(default="", description="Character fears and anxieties")
    relationships: str = Field(default="", description="Relationships with other characters")
    
    # Metadata
    is_hidden: bool = Field(default=False, description="Whether character is hidden from UI")
    last_modified: Optional[datetime] = Field(None, description="When character was last modified")


class CharacterState(BaseModel):
    name: str = Field(description="Character name")
    recent_actions: List[str] = Field(
        default_factory=list,
        description="Recent actions taken by the character"
    )
    recent_dialog: List[str] = Field(
        default_factory=list,
        description="Recent dialog by the character"
    )
    physicalSensations: List[str] = Field(
        default_factory=list,
        description="Recent physical sensations experienced by the character"
    )
    emotions: List[str] = Field(
        default_factory=list,
        description="Recent emotions experienced by the character"
    )
    internalMonologue: List[str] = Field(
        default_factory=list,
        description="Recent internal monologue by the character, what he thinks"
    )
    goals: List[str] = Field(
        default_factory=list,
        description="Character's current goals and objectives"
    )
    memories: List[str] = Field(
        default_factory=list,
        description="Important memories affecting current behavior"
    )


class OutlineItem(BaseModel):
    """Individual item in the story outline structure."""
    id: str = Field(description="Unique outline item identifier")
    type: Literal["chapter", "scene", "plot-point", "character-arc"] = Field(
        description="Type of outline item"
    )
    title: str = Field(description="Outline item title")
    description: str = Field(description="Detailed description")
    key_plot_items: List[str] = Field(
        default_factory=list,
        description="Detailed story beats for this item"
    )
    order: int = Field(description="Order position in the outline")
    parent_id: Optional[str] = Field(
        None,
        description="Parent item ID for hierarchical structure"
    )
    involved_characters: List[str] = Field(
        default_factory=list,
        description="Character names/IDs involved in this item"
    )


class OutlineFeedback(BaseModel):
    """Rater feedback on plot outline."""
    rater_id: str = Field(description="ID of the rater providing feedback")
    rater_name: str = Field(description="Name of the rater")
    feedback: str = Field(description="Feedback content")
    status: Literal["pending", "generating", "complete", "error"] = Field(
        description="Status of the feedback generation"
    )
    timestamp: datetime = Field(description="When feedback was provided")
    user_response: Optional[Literal["accepted", "revision_requested", "discussed"]] = Field(
        None,
        description="User's response to the feedback"
    )


class StoryOutline(BaseModel):
    """Complete story structure and outline information."""
    summary: Optional[str] = Field(None, description="Story summary")
    content: str = Field(description="Full outline text content")
    outline_items: List[OutlineItem] = Field(
        default_factory=list,
        description="Structured outline items"
    )
    chat_history: List[ChatMessage] = Field(
        default_factory=list,
        description="Outline development conversation history"
    )


class ChapterDetails(BaseModel):
    """Complete chapter information and associated feedback."""
    id: str = Field(description="Unique chapter identifier")
    number: int = Field(description="Chapter number")
    title: str = Field(description="Chapter title")
    content: str = Field(description="Chapter text content")
    
    # Plot context
    plot_point: Optional[str] = Field(
        None,
        description="Overall chapter theme or plot point"
    )
    key_plot_items: List[str] = Field(
        default_factory=list,
        description="Specific story beats within the chapter"
    )
    
    # Metadata
    created: datetime = Field(description="When the chapter was created")
    last_modified: datetime = Field(description="When the chapter was last modified")


class RequestContextMetadata(BaseModel):
    """Metadata about the request context for processing optimization."""
    story_id: str = Field(description="Unique story identifier")
    story_title: str = Field(description="Story title")
    version: Optional[str] = Field(None, description="Context version")
    created_at: Optional[datetime] = Field(None, description="When the context was created")
    total_characters: Optional[int] = Field(None, description="Total number of characters")
    total_chapters: Optional[int] = Field(None, description="Total number of chapters")


class RequestContext(BaseModel):
    """
    Comprehensive context object encapsulating all story state from frontend.
    
    This is the primary data structure for passing complete story information
    to backend API endpoints. It replaces the previous StructuredContextContainer
    with a richer, more complete representation that preserves all frontend
    information without transformation loss.
    
    The RequestContext includes:
    - Complete story configuration and system prompts
    - Full worldbuilding information with conversation history
    - Detailed character information and current state
    - Comprehensive story outline with hierarchical structure
    - Complete chapter content with all feedback types
    - Rich metadata for processing optimization
    """
    
    # === CONFIGURATION ===
    configuration: StoryConfiguration = Field(
        description="System prompts and agent configuration"
    )
    
    # === WORLDBUILDING ===
    worldbuilding: Optional[WorldbuildingInfo] = Field(
        None,
        description="Complete worldbuilding context and history"
    )
    
    # === CHARACTERS ===
    characters: List[CharacterDetails] = Field(
        default_factory=list,
        description="Complete character foundational information"
    )

    character_states: List[CharacterState] = Field(
        default_factory=list,
        description="Current state of each character"
    )
    
    # === STORY STRUCTURE ===
    story_outline: Optional[StoryOutline] = Field(
        None,
        description="Complete story structure and outline"
    )
    
    # === CHAPTERS ===
    chapters: List[ChapterDetails] = Field(
        default_factory=list,
        description="Complete chapter content and feedback"
    )
    
    # === METADATA ===
    context_metadata: RequestContextMetadata = Field(
        description="Context processing metadata and optimization hints"
    )
    
    # Pydantic V2 configuration using ConfigDict
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True
    )
