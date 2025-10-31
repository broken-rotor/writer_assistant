"""
Token counting API endpoints.

This module provides REST API endpoints for token counting functionality,
supporting batch processing, content type detection, and budget validation.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status

from app.models.token_models import (
    TokenCountRequest,
    TokenCountResponse,
    TokenCountResultItem,
    TokenValidationRequest,
    TokenValidationResponse,
    ErrorResponse
)
from app.services.token_management import TokenCounter
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def get_token_counter() -> TokenCounter:
    """Dependency to get TokenCounter instance."""
    return TokenCounter(model_path=settings.MODEL_PATH)


@router.post(
    "/count",
    response_model=TokenCountResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Count tokens for batch text inputs",
    description="""
    Count tokens for multiple text inputs using the Llama tokenizer.

    This endpoint supports:
    - Batch processing for efficiency (up to 50 texts per request)
    - Multiple content types (system prompts, narrative, dialogue, etc.)
    - Different counting strategies (exact, estimated, conservative, optimistic)
    - Comprehensive metadata including overhead calculations

    **Content Types:**
    - `system_prompt`: System instructions and prompts
    - `narrative`: Story narrative content
    - `dialogue`: Character dialogue
    - `character_description`: Character descriptions
    - `scene_description`: Scene and setting descriptions
    - `internal_monologue`: Character thoughts
    - `metadata`: Structured metadata
    - `unknown`: Auto-detected content type

    **Counting Strategies:**
    - `exact`: Precise token count (1.0x overhead)
    - `estimated`: Fast estimation with small overhead (1.1x)
    - `conservative`: Higher overhead for safety (1.25x)
    - `optimistic`: Lower overhead for efficiency (0.95x)

    **Example Usage:**
    ```json
    {
        "texts": [
            {
                "text": "You are a helpful writing assistant.",
                "content_type": "system_prompt"
            },
            {
                "text": "Once upon a time, in a distant kingdom...",
                "content_type": "narrative"
            }
        ],
        "strategy": "exact",
        "include_metadata": true
    }
    ```
    """,
    tags=["tokens"]
)
async def count_tokens(
    request: TokenCountRequest,
    token_counter: TokenCounter = Depends(get_token_counter)
) -> TokenCountResponse:
    """
    Count tokens for batch text inputs.

    Args:
        request: Token counting request with texts and options
        token_counter: TokenCounter service instance

    Returns:
        TokenCountResponse with results and summary

    Raises:
        HTTPException: For validation errors or processing failures
    """
    try:
        logger.info(f"Processing token count request for {len(request.texts)} texts")

        # Prepare inputs for batch processing
        texts = [item.text for item in request.texts]
        content_types = [item.content_type for item in request.texts]

        # Process batch token counting
        results = token_counter.count_tokens_batch(
            contents=texts,
            content_types=content_types,
            strategy=request.strategy
        )

        # Build response items
        response_items = []
        for i, result in enumerate(results):
            item = TokenCountResultItem(
                text=result.content,
                token_count=result.token_count,
                content_type=result.content_type,
                strategy=result.strategy,
                overhead_applied=result.overhead_applied,
                metadata=result.metadata if request.include_metadata else None
            )
            response_items.append(item)

        # Calculate summary statistics
        total_tokens = sum(r.token_count for r in results)
        total_chars = sum(len(r.content) for r in results)

        summary = {
            "total_texts": len(results),
            "total_tokens": total_tokens,
            "total_characters": total_chars,
            "avg_tokens_per_text": total_tokens / len(results) if results else 0,
            "avg_chars_per_text": total_chars / len(results) if results else 0,
            "avg_tokens_per_char": total_tokens / total_chars if total_chars > 0 else 0,
            "strategy_used": request.strategy.value,
            "tokenizer_ready": token_counter.tokenizer.is_ready()
        }

        # Add content type distribution if metadata requested
        if request.include_metadata:
            type_counts = {}
            for result in results:
                content_type = result.content_type
                type_counts[content_type.value] = type_counts.get(content_type.value, 0) + 1

            summary["content_type_distribution"] = {
                content_type: count / len(results)
                for content_type, count in type_counts.items()
            }

        logger.info(f"Successfully processed {len(results)} texts, total tokens: {total_tokens}")

        return TokenCountResponse(
            success=True,
            results=response_items,
            summary=summary
        )

    except ValueError as e:
        logger.error(f"Validation error in token counting: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error in token counting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error"}
        )


@router.post(
    "/validate",
    response_model=TokenValidationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Validate texts against token budget",
    description="""
    Validate whether a list of texts fits within a specified token budget.

    This endpoint is useful for:
    - Pre-flight validation before sending to LLM
    - Budget planning for multi-part prompts
    - Ensuring content fits within context windows

    Uses conservative counting strategy by default for safety.

    **Example Usage:**
    ```json
    {
        "texts": [
            "System prompt text here",
            "User input text here",
            "Assistant response text here"
        ],
        "budget": 4096,
        "strategy": "conservative"
    }
    ```
    """,
    tags=["tokens"]
)
async def validate_token_budget(
    request: TokenValidationRequest,
    token_counter: TokenCounter = Depends(get_token_counter)
) -> TokenValidationResponse:
    """
    Validate texts against a token budget.

    Args:
        request: Token validation request with texts and budget
        token_counter: TokenCounter service instance

    Returns:
        TokenValidationResponse with validation results

    Raises:
        HTTPException: For validation errors or processing failures
    """
    try:
        logger.info(f"Validating {len(request.texts)} texts against budget of {request.budget}")

        # Validate token budget using the service
        validation_result = token_counter.validate_token_budget(
            contents=request.texts,
            budget=request.budget,
            strategy=request.strategy
        )

        logger.info(f"Validation result: {validation_result['fits_budget']}, "
                    f"tokens: {validation_result['total_tokens']}/{request.budget}")

        return TokenValidationResponse(
            success=True,
            fits_budget=validation_result["fits_budget"],
            total_tokens=validation_result["total_tokens"],
            budget=validation_result["budget"],
            utilization=validation_result["utilization"],
            remaining_tokens=validation_result["remaining_tokens"],
            overflow_tokens=validation_result["overflow_tokens"],
            strategy_used=request.strategy
        )

    except ValueError as e:
        logger.error(f"Validation error in budget validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error in budget validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error"}
        )


@router.get(
    "/strategies",
    response_model=Dict[str, Any],
    summary="Get available counting strategies and token limits",
    description="""
    Get information about available token counting strategies, content types, and system token limits.

    Returns:
    - Available counting strategies with descriptions
    - Available content types with descriptions
    - System token limits and context window sizes
    - Default configurations and overhead multipliers
    """,
    tags=["tokens"]
)
async def get_strategies() -> Dict[str, Any]:
    """
    Get available counting strategies, content types, and system token limits.

    Returns:
        Dictionary with available strategies, content types, and token limits
    """
    try:
        strategies = {
            "exact": {
                "description": "Precise token count using tokenizer",
                "overhead": 1.0,
                "use_case": "When you need exact token counts"
            },
            "estimated": {
                "description": "Fast estimation with small overhead",
                "overhead": 1.1,
                "use_case": "For quick estimates with slight safety margin"
            },
            "conservative": {
                "description": "Higher overhead for safety",
                "overhead": 1.25,
                "use_case": "When you want to ensure you don't exceed limits"
            },
            "optimistic": {
                "description": "Lower overhead for efficiency",
                "overhead": 0.95,
                "use_case": "When you want to maximize content within limits"
            }
        }

        content_types = {
            "narrative": {
                "description": "Story narrative content",
                "multiplier": 1.0
            },
            "dialogue": {
                "description": "Character dialogue",
                "multiplier": 1.05
            },
            "system_prompt": {
                "description": "System instructions and prompts",
                "multiplier": 1.15
            },
            "character_description": {
                "description": "Character descriptions",
                "multiplier": 1.0
            },
            "scene_description": {
                "description": "Scene and setting descriptions",
                "multiplier": 1.0
            },
            "internal_monologue": {
                "description": "Character thoughts",
                "multiplier": 1.0
            },
            "metadata": {
                "description": "Structured metadata",
                "multiplier": 1.2
            },
            "unknown": {
                "description": "Auto-detected content type",
                "multiplier": 1.1
            }
        }

        # Expose system token limits for frontend use
        token_limits = {
            "llm_context_window": settings.LLM_N_CTX,
            "llm_max_generation": settings.LLM_MAX_TOKENS,
            "context_management": {
                "max_context_tokens": settings.CONTEXT_MAX_TOKENS,
                "buffer_tokens": settings.CONTEXT_BUFFER_TOKENS,
                "layer_limits": {
                    "system_instructions": settings.CONTEXT_LAYER_A_TOKENS,
                    "immediate_instructions": settings.CONTEXT_LAYER_B_TOKENS,
                    "recent_story": settings.CONTEXT_LAYER_C_TOKENS,
                    "character_scene_data": settings.CONTEXT_LAYER_D_TOKENS,
                    "plot_world_summary": settings.CONTEXT_LAYER_E_TOKENS
                }
            },
            "recommended_limits": {
                "system_prompt_prefix": settings.CONTEXT_LAYER_A_TOKENS // 4,  # ~500 tokens
                "system_prompt_suffix": settings.CONTEXT_LAYER_A_TOKENS // 4,  # ~500 tokens
                "writing_assistant_prompt": settings.CONTEXT_LAYER_A_TOKENS // 2,  # ~1000 tokens
                "writing_editor_prompt": settings.CONTEXT_LAYER_A_TOKENS // 2   # ~1000 tokens
            }
        }

        return {
            "success": True,
            "strategies": strategies,
            "content_types": content_types,
            "token_limits": token_limits,
            "default_strategy": "exact",
            "batch_limits": {
                "max_texts_per_request": 50,
                "max_text_size_bytes": 100000
            }
        }

    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error"}
        )
