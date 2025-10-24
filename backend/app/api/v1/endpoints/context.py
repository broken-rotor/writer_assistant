"""
Context management endpoints for Writer Assistant.

This module provides API endpoints for context management operations including
context optimization, analysis, validation, and health checks.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from app.models.context_models import (
    ContextManageRequest, ContextManageResponse, ContextHealthCheckResponse,
    ContextErrorResponse, ContextItemRequest, ContextTypeEnum, LayerTypeEnum
)
from app.services.context_manager import (
    ContextManager, ContextItem, ContextType, ContextAnalysis
)
from app.services.token_management import LayerType
from app.api.v1.endpoints.request_validators import ContextValidator
from app.api.v1.endpoints.response_formatters import (
    ResponseFormatter, format_validation_errors, measure_processing_time
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances (in production, these would be dependency-injected)
context_manager = ContextManager()
context_validator = ContextValidator(context_manager)
response_formatter = ResponseFormatter()


def get_context_manager() -> ContextManager:
    """Dependency to get ContextManager instance."""
    return context_manager


def get_context_validator() -> ContextValidator:
    """Dependency to get ContextValidator instance."""
    return context_validator


def get_response_formatter() -> ResponseFormatter:
    """Dependency to get ResponseFormatter instance."""
    return response_formatter


@router.post("/manage", response_model=ContextManageResponse)
async def manage_context(
    request: ContextManageRequest,
    cm: ContextManager = Depends(get_context_manager),
    validator: ContextValidator = Depends(get_context_validator),
    formatter: ResponseFormatter = Depends(get_response_formatter)
):
    """
    Manage and optimize context items for AI generation.
    
    This endpoint accepts context items, validates them, analyzes token usage,
    and optionally applies optimization techniques including context distillation
    and compression to fit within specified token budgets.
    
    Args:
        request: Context management request with items and optimization settings
        cm: ContextManager dependency
        validator: ContextValidator dependency
        formatter: ResponseFormatter dependency
        
    Returns:
        ContextManageResponse with analysis, optimization results, and statistics
        
    Raises:
        HTTPException: For validation errors or processing failures
    """
    start_time = time.time()
    request_id = f"ctx_{int(start_time * 1000)}"
    
    try:
        logger.info(f"Processing context management request {request_id} with {len(request.context_items)} items")
        
        # Validate the request
        is_valid, validation_errors = validator.validate_context_request(request)
        if not is_valid:
            logger.warning(f"Request {request_id} validation failed: {len(validation_errors)} errors")
            error_details = format_validation_errors(validation_errors)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ContextErrorResponse(
                    error="Request validation failed",
                    details=error_details,
                    request_id=request_id
                ).dict()
            )
        
        # Convert request items to ContextItem objects
        context_items = []
        for item in request.context_items:
            try:
                context_items.append(ContextItem(
                    content=item.content,
                    context_type=ContextType(item.context_type.value),
                    priority=item.priority,
                    layer_type=LayerType(item.layer_type.value),
                    metadata=item.metadata or {}
                ))
            except Exception as e:
                logger.error(f"Error converting context item: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid context item: {str(e)}"
                )
        
        # Analyze context
        try:
            analysis = cm.analyze_context(context_items)
            logger.info(f"Context analysis complete: {analysis.total_tokens} tokens, optimization_needed={analysis.optimization_needed}")
        except Exception as e:
            logger.error(f"Context analysis failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Context analysis failed: {str(e)}"
            )
        
        # Apply optimization if requested and needed
        optimization_result = None
        if request.enable_compression and (analysis.optimization_needed or request.target_tokens):
            try:
                logger.info(f"Applying context optimization with target_tokens={request.target_tokens}")
                optimization_result = cm.optimize_context(
                    context_items=context_items,
                    target_tokens=request.target_tokens
                )
                logger.info(f"Optimization complete: {optimization_result.original_tokens} -> {optimization_result.optimized_tokens} tokens")
            except Exception as e:
                logger.error(f"Context optimization failed: {str(e)}")
                # Don't fail the entire request if optimization fails
                logger.warning("Continuing without optimization due to error")
        
        # Calculate processing time
        processing_time_ms = measure_processing_time(start_time)
        
        # Format response
        try:
            response = formatter.format_context_manage_response(
                analysis=analysis,
                optimization_result=optimization_result,
                validation_errors=None,
                processing_time_ms=processing_time_ms,
                success=True,
                message="Context management completed successfully"
            )
            
            logger.info(f"Request {request_id} completed successfully in {processing_time_ms:.2f}ms")
            return response
            
        except Exception as e:
            logger.error(f"Response formatting failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Response formatting failed: {str(e)}"
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in context management: {str(e)}")
        processing_time_ms = measure_processing_time(start_time)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ContextErrorResponse(
                error=f"Internal server error: {str(e)}",
                request_id=request_id
            ).dict()
        )


@router.get("/health", response_model=ContextHealthCheckResponse)
async def health_check(
    cm: ContextManager = Depends(get_context_manager),
    formatter: ResponseFormatter = Depends(get_response_formatter)
):
    """
    Health check endpoint for context management services.
    
    Returns the status of all context management components including
    token management, context distillation, and layer hierarchy services.
    
    Args:
        cm: ContextManager dependency
        formatter: ResponseFormatter dependency
        
    Returns:
        ContextHealthCheckResponse with service status and configuration
    """
    try:
        logger.debug("Performing context management health check")
        response = formatter.format_health_check_response(cm)
        
        # Return appropriate HTTP status based on health
        if response.status == "healthy":
            return response
        elif response.status == "degraded":
            return JSONResponse(
                status_code=status.HTTP_206_PARTIAL_CONTENT,
                content=response.dict()
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=response.dict()
            )
            
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ContextHealthCheckResponse(
                status="error",
                version="1.0.0",
                services={"error": str(e)},
                configuration={}
            ).dict()
        )


@router.post("/analyze")
async def analyze_context(
    request: ContextManageRequest,
    cm: ContextManager = Depends(get_context_manager),
    validator: ContextValidator = Depends(get_context_validator)
):
    """
    Analyze context items without applying optimization.
    
    This endpoint provides context analysis including token counts,
    optimization recommendations, and statistics without modifying
    the original content.
    
    Args:
        request: Context management request with items to analyze
        cm: ContextManager dependency
        validator: ContextValidator dependency
        
    Returns:
        Context analysis results and statistics
        
    Raises:
        HTTPException: For validation errors or analysis failures
    """
    start_time = time.time()
    request_id = f"analyze_{int(start_time * 1000)}"
    
    try:
        logger.info(f"Analyzing context request {request_id} with {len(request.context_items)} items")
        
        # Basic validation (less strict than full management)
        if not request.context_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one context item is required"
            )
        
        # Convert to ContextItem objects
        context_items = []
        for item in request.context_items:
            try:
                context_items.append(ContextItem(
                    content=item.content,
                    context_type=ContextType(item.context_type.value),
                    priority=item.priority,
                    layer_type=LayerType(item.layer_type.value),
                    metadata=item.metadata or {}
                ))
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid context item: {str(e)}"
                )
        
        # Perform analysis
        analysis = cm.analyze_context(context_items)
        statistics = cm.get_context_statistics(context_items)
        
        processing_time_ms = measure_processing_time(start_time)
        
        response = {
            "success": True,
            "message": "Context analysis completed",
            "analysis": {
                "total_tokens": analysis.total_tokens,
                "total_items": len(context_items),
                "tokens_by_type": {ct.value: count for ct, count in analysis.tokens_by_type.items()},
                "tokens_by_layer": {lt.value: count for lt, count in analysis.tokens_by_layer.items()},
                "optimization_needed": analysis.optimization_needed,
                "compression_candidates": analysis.compression_candidates,
                "recommendations": analysis.recommendations,
                "utilization_ratio": analysis.total_tokens / cm.max_context_tokens
            },
            "statistics": statistics,
            "processing_time_ms": processing_time_ms,
            "request_id": request_id
        }
        
        logger.info(f"Analysis request {request_id} completed in {processing_time_ms:.2f}ms")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Context analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/validate")
async def validate_context(
    request: ContextManageRequest,
    validator: ContextValidator = Depends(get_context_validator)
):
    """
    Validate context items without processing them.
    
    This endpoint validates the structure, content, and relationships
    of context items and returns detailed validation results.
    
    Args:
        request: Context management request to validate
        validator: ContextValidator dependency
        
    Returns:
        Validation results with errors and warnings
    """
    start_time = time.time()
    request_id = f"validate_{int(start_time * 1000)}"
    
    try:
        logger.info(f"Validating context request {request_id} with {len(request.context_items)} items")
        
        # Perform comprehensive validation
        is_valid, validation_errors = validator.validate_context_request(request)
        
        processing_time_ms = measure_processing_time(start_time)
        
        response = {
            "success": True,
            "message": "Validation completed",
            "validation": {
                "is_valid": is_valid,
                "errors": validation_errors,
                "warnings": []
            },
            "processing_time_ms": processing_time_ms,
            "request_id": request_id
        }
        
        logger.info(f"Validation request {request_id} completed: valid={is_valid}, errors={len(validation_errors)}")
        return response
        
    except Exception as e:
        logger.error(f"Context validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@router.get("/config")
async def get_configuration(
    cm: ContextManager = Depends(get_context_manager)
):
    """
    Get current context management configuration.
    
    Returns the current configuration settings for the context manager
    including token limits, thresholds, and optimization settings.
    
    Args:
        cm: ContextManager dependency
        
    Returns:
        Current configuration settings
    """
    try:
        config = {
            "max_context_tokens": cm.max_context_tokens,
            "distillation_threshold": cm.distillation_threshold,
            "enable_compression": cm.enable_compression,
            "version": "1.0.0",
            "supported_context_types": [ct.value for ct in ContextTypeEnum],
            "supported_layer_types": [lt.value for lt in LayerTypeEnum],
            "optimization_modes": ["aggressive", "balanced", "conservative"]
        }
        
        return {
            "success": True,
            "message": "Configuration retrieved successfully",
            "configuration": config
        }
        
    except Exception as e:
        logger.error(f"Failed to get configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )
