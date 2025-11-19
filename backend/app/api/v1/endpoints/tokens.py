"""
Token counting API endpoints.

This module provides REST API endpoints for token counting functionality,
supporting batch processing, content type detection, and budget validation.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status

from app.models.token_models import (
    TokenCountRequest,
    TokenCountResponse,
    TokenCountResultItem,
    TokenValidationRequest,
    TokenValidationResponse,
    ErrorResponse
)
from app.services.llm_inference import get_llm
from app.services.token_counter import TokenCounter

logger = logging.getLogger(__name__)

router = APIRouter()


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
                "text": "You are a helpful writing assistant."
            },
            {
                "text": "Once upon a time, in a distant kingdom..."
            }
        ]
    }
    ```
    """,
    tags=["tokens"]
)
async def count_tokens(request: TokenCountRequest) -> TokenCountResponse:
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
    llm = get_llm()
    if not llm:
        raise HTTPException(
            status_code=503,
            detail="LLM not initialized. Start server with --model-path")
    token_counter = TokenCounter(llm)

    try:
        logger.info(f"Processing token count request for {len(request.texts)} texts")

        # Prepare inputs for batch processing
        texts = [item.text for item in request.texts]

        # Process batch token counting
        results = token_counter.count_tokens_batch(texts)

        # Build response items
        response_items = []
        for i, result in enumerate(results):
            item = TokenCountResultItem(
                text=texts[i],
                token_count=result
            )
            response_items.append(item)

        return TokenCountResponse(
            success=True,
            results=response_items
        )

    except ValueError as e:
        logger.exception(f"Validation error in token counting")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.exception(f"Unexpected error in token counting")
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
async def validate_token_budget(request: TokenValidationRequest) -> TokenValidationResponse:
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
    llm = get_llm()
    if not llm:
        raise HTTPException(
            status_code=503,
            detail="LLM not initialized. Start server with --model-path")
    token_counter = TokenCounter(llm)

    try:
        logger.info(f"Validating {len(request.texts)} texts against budget of {request.budget}")

        # Validate token budget using the service
        validation_result = token_counter.validate_token_budget(
            contents=request.texts,
            budget=request.budget
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
            overflow_tokens=validation_result["overflow_tokens"]
        )

    except ValueError as e:
        logger.exception("Validation error in budget validation")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.exception("Unexpected error in budget validation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error"}
        )
