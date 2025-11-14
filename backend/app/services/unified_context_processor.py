"""
Unified Context Processor for Writer Assistant API.

This service provides a unified interface for processing RequestContext objects
for use by the ContextManager service.

Key Features:
- RequestContext processing and validation
- Context metadata generation
- Performance optimization with caching
- Comprehensive error handling and fallback logic
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Literal
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json

from app.services.context_manager import ContextManager
from app.services.plot_outline_extractor import get_plot_outline_extractor
from app.core.config import settings
from app.models.context_models import (
    ContextProcessingConfig,
    AgentType
)
from app.models.generation_models import (
    SystemPrompts,
    CharacterInfo,
    ChapterInfo,
    FeedbackItem,
    ContextMetadata,
)
from app.models.request_context import RequestContext

logger = logging.getLogger(__name__)


@dataclass
class UnifiedContextResult:
    """Result of unified context processing."""
    system_prompt: str
    user_message: str
    context_metadata: Dict[str, Any]
    processing_time: float
    cache_hit: bool = False


class UnifiedContextProcessor:
    """
    Unified context processor that handles RequestContext objects.
    
    This processor works with the new RequestContext structure and provides
    a clean interface for context processing without legacy dependencies.
    """

    def __init__(self, enable_caching: bool = True):
        """Initialize the unified context processor."""
        self.context_manager = ContextManager()
        self.plot_outline_extractor = get_plot_outline_extractor()
        self.enable_caching = enable_caching
        self._cache = {}

        logger.info("UnifiedContextProcessor initialized")

    def _process_request_context(
        self, 
        request_context: RequestContext
    ) -> Dict[str, Any]:
        """
        Process RequestContext for internal use.
        
        This method extracts and organizes information from RequestContext
        for use by the ContextManager and other services.
        """
        if request_context is None:
            return {
                "context_data": {},
                "metadata": {
                    "total_elements": 0,
                    "processing_applied": False,
                    "processing_mode": "request_context",
                    "optimization_level": "none"
                }
            }
        
        # Extract context data from RequestContext
        context_data = {
            "story_outline": request_context.story_outline.summary if request_context.story_outline else None,
            "characters": [char.model_dump() for char in request_context.characters] if request_context.characters else [],
            "worldbuilding": request_context.worldbuilding.content if request_context.worldbuilding else None,
            "configuration": request_context.configuration.model_dump() if request_context.configuration else {},
            "context_metadata": request_context.context_metadata.model_dump() if request_context.context_metadata else {}
        }
        
        return {
            "context_data": context_data,
            "metadata": {
                "total_elements": len(context_data.get("characters", [])) + (1 if context_data.get("story_outline") else 0),
                "processing_applied": True,
                "processing_mode": "request_context",
                "optimization_level": "standard"
            }
        }

    def process_generate_chapter_context(
        self,
        request_context: Optional[RequestContext],
        context_processing_config: Optional[ContextProcessingConfig] = None
    ) -> UnifiedContextResult:
        """
        Process context for chapter generation with full narrative context assembly.

        This method implements the endpoint-specific context assembly strategy
        for chapter generation, prioritizing narrative flow and character development.
        """
        try:
            start_time = datetime.now()

            # Use context manager to process context for WRITER agent
            config = context_processing_config or ContextProcessingConfig()
            formatted_context, metadata = self.context_manager.process_context_for_agent(
                request_context=request_context,
                config=config,
                agent_type=AgentType.WRITER
            )

            # Parse into system prompt and user message
            system_prompt, user_message = self._parse_formatted_context(
                formatted_context,
                AgentType.WRITER,
                "chapter_generation"
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            return UnifiedContextResult(
                system_prompt=system_prompt,
                user_message=user_message,
                context_metadata=metadata,
                processing_time=processing_time,
                cache_hit=False
            )

        except Exception as e:
            logger.error(f"Error processing chapter generation context: {str(e)}")
            return self._create_error_result(str(e))

    def process_character_feedback_context(
        self,
        request_context: Optional[RequestContext],
        context_processing_config: Optional[ContextProcessingConfig] = None
    ) -> UnifiedContextResult:
        """Process context for character feedback generation."""
        try:
            start_time = datetime.now()

            # Use context manager to process context for CHARACTER agent
            config = context_processing_config or ContextProcessingConfig()
            formatted_context, metadata = self.context_manager.process_context_for_agent(
                request_context=request_context,
                config=config,
                agent_type=AgentType.CHARACTER
            )

            system_prompt, user_message = self._parse_formatted_context(
                formatted_context,
                AgentType.CHARACTER,
                "character_feedback"
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            return UnifiedContextResult(
                system_prompt=system_prompt,
                user_message=user_message,
                context_metadata=metadata,
                processing_time=processing_time,
                cache_hit=False
            )

        except Exception as e:
            logger.error(f"Error processing character feedback context: {str(e)}")
            return self._create_error_result(str(e))

    def _parse_formatted_context(
        self,
        formatted_context: str,
        agent_type: AgentType,
        endpoint_strategy: str
    ) -> Tuple[str, str]:
        """
        Parse formatted context from ContextManager into system prompt and user message.

        The ContextManager returns a formatted string that needs to be split into
        system prompt and user message components based on the agent type and strategy.
        """
        # Split the formatted context into sections
        sections = formatted_context.split("\n=== ")

        system_sections = []
        user_sections = []

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Add back the === prefix that was removed by split
            if not section.startswith("==="):
                section = "=== " + section

            # Categorize sections based on content
            if any(keyword in section.upper() for keyword in [
                "SYSTEM INSTRUCTIONS", "EDITORIAL GUIDELINES", "EVALUATION CRITERIA"
            ]):
                system_sections.append(section)
            else:
                user_sections.append(section)

        # Build system prompt and user message
        system_prompt = "\n\n".join(
            system_sections) if system_sections else "You are a helpful AI assistant."
        user_message = "\n\n".join(
            user_sections) if user_sections else formatted_context

        return system_prompt, user_message

    def _create_error_result(self, error_message: str) -> UnifiedContextResult:
        """Create an error result for failed context processing."""
        return UnifiedContextResult(
            system_prompt="You are a helpful AI assistant.",
            user_message=f"Error processing context: {error_message}",
            context_metadata={
                "error": True,
                "error_message": error_message,
                "total_elements": 0,
                "processing_applied": False
            },
            processing_time=0.0,
            cache_hit=False
        )

    def clear_cache(self):
        """Clear the context processing cache."""
        self._cache.clear()
        logger.info("Context processing cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._cache),
            "cache_enabled": self.enable_caching
        }


# Global instance
_unified_context_processor = None


def get_unified_context_processor() -> UnifiedContextProcessor:
    """Get the global unified context processor instance."""
    global _unified_context_processor
    if _unified_context_processor is None:
        _unified_context_processor = UnifiedContextProcessor()
    return _unified_context_processor
