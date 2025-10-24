"""
Request validation utilities for context management and generation endpoints.

This module provides reusable validation functions for context data types,
token limits, content structure, and data integrity checks.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from pydantic import ValidationError

from app.models.context_models import (
    ContextItemRequest, ContextManageRequest, ContextTypeEnum, LayerTypeEnum
)
from app.services.context_manager import ContextManager, ContextItem, ContextType
from app.services.token_management import LayerType

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error with detailed information."""
    def __init__(self, message: str, field: Optional[str] = None, code: str = "VALIDATION_ERROR"):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(message)


class ContextValidator:
    """Validator for context management requests and data."""
    
    def __init__(self, context_manager: Optional[ContextManager] = None):
        """
        Initialize the validator.
        
        Args:
            context_manager: Optional ContextManager instance for advanced validation
        """
        self.context_manager = context_manager or ContextManager()
    
    def validate_context_request(self, request: ContextManageRequest) -> Tuple[bool, List[str]]:
        """
        Validate a complete context management request.
        
        Args:
            request: The context management request to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Validate individual context items
            for i, item in enumerate(request.context_items):
                item_errors = self.validate_context_item(item)
                for error in item_errors:
                    errors.append(f"Item {i}: {error}")
            
            # Validate context item relationships
            relationship_errors = self.validate_context_relationships(request.context_items)
            errors.extend(relationship_errors)
            
            # Validate token constraints
            if request.target_tokens:
                token_errors = self.validate_token_constraints(request.context_items, request.target_tokens)
                errors.extend(token_errors)
            
            # Validate optimization settings
            optimization_errors = self.validate_optimization_settings(request)
            errors.extend(optimization_errors)
            
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.debug("Context request validation passed")
            else:
                logger.warning(f"Context request validation failed: {len(errors)} errors")
            
            return is_valid, errors
            
        except Exception as e:
            logger.error(f"Error validating context request: {str(e)}")
            return False, [f"Validation error: {str(e)}"]
    
    def validate_context_item(self, item: ContextItemRequest) -> List[str]:
        """
        Validate an individual context item.
        
        Args:
            item: The context item to validate
            
        Returns:
            List of error messages
        """
        errors = []
        
        try:
            # Content validation
            if not item.content or len(item.content.strip()) == 0:
                errors.append("Content cannot be empty")
            elif len(item.content) > 50000:  # Reasonable upper limit
                errors.append("Content exceeds maximum length (50,000 characters)")
            
            # Context type validation
            if item.context_type not in ContextTypeEnum:
                errors.append(f"Invalid context type: {item.context_type}")
            
            # Layer type validation
            if item.layer_type not in LayerTypeEnum:
                errors.append(f"Invalid layer type: {item.layer_type}")
            
            # Priority validation
            if item.priority < 0 or item.priority > 100:
                errors.append("Priority must be between 0 and 100")
            
            # Metadata validation
            if item.metadata:
                metadata_errors = self.validate_metadata(item.metadata)
                errors.extend(metadata_errors)
            
            # Content-specific validation
            content_errors = self.validate_content_by_type(item.content, item.context_type)
            errors.extend(content_errors)
            
        except Exception as e:
            errors.append(f"Item validation error: {str(e)}")
        
        return errors
    
    def validate_context_relationships(self, items: List[ContextItemRequest]) -> List[str]:
        """
        Validate relationships and dependencies between context items.
        
        Args:
            items: List of context items to validate
            
        Returns:
            List of error messages
        """
        errors = []
        
        try:
            # Check for required context types
            present_types = {item.context_type for item in items}
            
            if ContextTypeEnum.SYSTEM not in present_types:
                errors.append("At least one SYSTEM context item is required")
            
            # Check for reasonable distribution
            type_counts = {}
            for item in items:
                type_counts[item.context_type] = type_counts.get(item.context_type, 0) + 1
            
            # Warn about excessive items of one type
            for context_type, count in type_counts.items():
                if count > 10:
                    errors.append(f"Excessive number of {context_type.value} items ({count}). Consider consolidation.")
            
            # Check layer distribution
            layer_counts = {}
            for item in items:
                layer_counts[item.layer_type] = layer_counts.get(item.layer_type, 0) + 1
            
            # Ensure working memory isn't overloaded
            working_memory_count = layer_counts.get(LayerTypeEnum.WORKING_MEMORY, 0)
            if working_memory_count > 5:
                errors.append(f"Too many items in working memory ({working_memory_count}). Consider using other layers.")
            
        except Exception as e:
            errors.append(f"Relationship validation error: {str(e)}")
        
        return errors
    
    def validate_token_constraints(self, items: List[ContextItemRequest], target_tokens: int) -> List[str]:
        """
        Validate token count constraints.
        
        Args:
            items: List of context items
            target_tokens: Target token count
            
        Returns:
            List of error messages
        """
        errors = []
        
        try:
            # Convert to ContextItem objects for analysis
            context_items = []
            for item in items:
                context_items.append(ContextItem(
                    content=item.content,
                    context_type=ContextType(item.context_type.value),
                    priority=item.priority,
                    layer_type=LayerType(item.layer_type.value),
                    metadata=item.metadata or {}
                ))
            
            # Analyze token usage
            analysis = self.context_manager.analyze_context(context_items)
            
            # Check if target is achievable
            if target_tokens < 1000:
                errors.append("Target token count too low (minimum 1000)")
            elif target_tokens > 16000:
                errors.append("Target token count too high (maximum 16000)")
            
            # Check if current content can be compressed to target
            if analysis.total_tokens > target_tokens * 3:
                errors.append(f"Content ({analysis.total_tokens} tokens) may be too large to compress to target ({target_tokens} tokens)")
            
            # Check for unrealistic compression requirements
            compression_ratio = target_tokens / analysis.total_tokens if analysis.total_tokens > 0 else 1.0
            if compression_ratio < 0.1:
                errors.append("Requested compression ratio too aggressive (< 0.1)")
            
        except Exception as e:
            errors.append(f"Token constraint validation error: {str(e)}")
        
        return errors
    
    def validate_optimization_settings(self, request: ContextManageRequest) -> List[str]:
        """
        Validate optimization settings and parameters.
        
        Args:
            request: The context management request
            
        Returns:
            List of error messages
        """
        errors = []
        
        try:
            # Validate optimization mode
            valid_modes = ["aggressive", "balanced", "conservative"]
            if request.optimization_mode not in valid_modes:
                errors.append(f"Invalid optimization mode: {request.optimization_mode}")
            
            # Validate preserve types
            for preserve_type in request.preserve_types:
                if preserve_type not in ContextTypeEnum:
                    errors.append(f"Invalid preserve type: {preserve_type}")
            
            # Check for conflicting settings
            if not request.enable_compression and request.target_tokens:
                # Calculate if target is achievable without compression
                context_items = []
                for item in request.context_items:
                    context_items.append(ContextItem(
                        content=item.content,
                        context_type=ContextType(item.context_type.value),
                        priority=item.priority,
                        layer_type=LayerType(item.layer_type.value),
                        metadata=item.metadata or {}
                    ))
                
                analysis = self.context_manager.analyze_context(context_items)
                if analysis.total_tokens > request.target_tokens:
                    errors.append("Target tokens cannot be achieved without compression")
            
        except Exception as e:
            errors.append(f"Optimization settings validation error: {str(e)}")
        
        return errors
    
    def validate_content_by_type(self, content: str, context_type: ContextTypeEnum) -> List[str]:
        """
        Validate content based on its context type.
        
        Args:
            content: The content to validate
            context_type: The type of context
            
        Returns:
            List of error messages
        """
        errors = []
        
        try:
            if context_type == ContextTypeEnum.SYSTEM:
                # System context should contain prompts or instructions
                if not any(keyword in content.lower() for keyword in ["prompt", "instruction", "system", "role"]):
                    errors.append("SYSTEM context should contain prompts or instructions")
            
            elif context_type == ContextTypeEnum.CHARACTER:
                # Character context should contain character information
                if not any(keyword in content.lower() for keyword in ["character", "name", "personality", "bio"]):
                    errors.append("CHARACTER context should contain character information")
            
            elif context_type == ContextTypeEnum.WORLD:
                # World context should contain world-building information
                if not any(keyword in content.lower() for keyword in ["world", "setting", "location", "environment"]):
                    errors.append("WORLD context should contain world-building information")
            
            elif context_type == ContextTypeEnum.STORY:
                # Story context should contain narrative information
                if not any(keyword in content.lower() for keyword in ["story", "plot", "narrative", "chapter"]):
                    errors.append("STORY context should contain narrative information")
            
            # Check for potentially problematic content
            if len(content.split()) < 5:
                errors.append("Content appears too short to be meaningful")
            
            # Check for encoding issues
            try:
                content.encode('utf-8')
            except UnicodeEncodeError:
                errors.append("Content contains invalid characters")
            
        except Exception as e:
            errors.append(f"Content type validation error: {str(e)}")
        
        return errors
    
    def validate_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """
        Validate metadata structure and content.
        
        Args:
            metadata: The metadata to validate
            
        Returns:
            List of error messages
        """
        errors = []
        
        try:
            # Check metadata size
            if len(str(metadata)) > 10000:
                errors.append("Metadata too large (maximum 10KB)")
            
            # Check for reserved keys
            reserved_keys = ["_internal", "_system", "_context_manager"]
            for key in metadata.keys():
                if key.startswith("_") and key in reserved_keys:
                    errors.append(f"Reserved metadata key: {key}")
            
            # Validate metadata values
            for key, value in metadata.items():
                if not isinstance(key, str):
                    errors.append("Metadata keys must be strings")
                
                # Check for complex nested structures
                if isinstance(value, (dict, list)) and len(str(value)) > 1000:
                    errors.append(f"Metadata value for '{key}' too complex")
            
        except Exception as e:
            errors.append(f"Metadata validation error: {str(e)}")
        
        return errors


def validate_generation_request_context(
    worldbuilding: str,
    story_summary: str,
    characters: List[Dict[str, Any]],
    system_prompts: Dict[str, str],
    feedback: List[Dict[str, Any]] = None
) -> Tuple[bool, List[str]]:
    """
    Validate context data from existing generation endpoints.
    
    Args:
        worldbuilding: World building information
        story_summary: Story summary
        characters: Character information
        system_prompts: System prompts
        feedback: Optional feedback items
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    try:
        # Validate required fields
        if not worldbuilding or not worldbuilding.strip():
            errors.append("Worldbuilding cannot be empty")
        
        if not story_summary or not story_summary.strip():
            errors.append("Story summary cannot be empty")
        
        if not characters:
            errors.append("At least one character is required")
        
        if not system_prompts:
            errors.append("System prompts are required")
        
        # Validate character structure
        for i, character in enumerate(characters):
            if not isinstance(character, dict):
                errors.append(f"Character {i}: Must be a dictionary")
                continue
            
            required_fields = ["name", "basicBio"]
            for field in required_fields:
                if field not in character or not character[field]:
                    errors.append(f"Character {i}: Missing required field '{field}'")
        
        # Validate system prompts structure
        if isinstance(system_prompts, dict):
            if "mainPrefix" not in system_prompts:
                errors.append("System prompts missing 'mainPrefix'")
        else:
            errors.append("System prompts must be a dictionary")
        
        # Validate feedback if provided
        if feedback:
            for i, feedback_item in enumerate(feedback):
                if not isinstance(feedback_item, dict):
                    errors.append(f"Feedback {i}: Must be a dictionary")
                    continue
                
                required_feedback_fields = ["content", "source"]
                for field in required_feedback_fields:
                    if field not in feedback_item:
                        errors.append(f"Feedback {i}: Missing required field '{field}'")
        
        # Check content lengths
        if len(worldbuilding) > 20000:
            errors.append("Worldbuilding too long (maximum 20,000 characters)")
        
        if len(story_summary) > 10000:
            errors.append("Story summary too long (maximum 10,000 characters)")
        
        is_valid = len(errors) == 0
        return is_valid, errors
        
    except Exception as e:
        logger.error(f"Error validating generation request context: {str(e)}")
        return False, [f"Validation error: {str(e)}"]
