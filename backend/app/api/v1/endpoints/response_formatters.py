"""
Response formatting utilities for context management and generation endpoints.

This module provides reusable formatting functions for consistent API responses,
error handling, and context statistics presentation.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

from app.models.context_models import (
    ContextManageResponse, ContextAnalysisResponse, ContextOptimizationResponse,
    ContextValidationResponse, ContextStatistics, ContextErrorResponse,
    ContextErrorDetail, ContextHealthCheckResponse, OptimizedContextData
)
from app.services.context_manager import (
    ContextAnalysis, ContextOptimizationResult, ContextManager
)

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Formatter for context management API responses."""
    
    def __init__(self):
        """Initialize the response formatter."""
        self.version = "1.0.0"
    
    def format_context_manage_response(
        self,
        analysis: ContextAnalysis,
        optimization_result: Optional[ContextOptimizationResult] = None,
        validation_errors: List[str] = None,
        processing_time_ms: float = 0,
        success: bool = True,
        message: str = "Context management completed successfully"
    ) -> ContextManageResponse:
        """
        Format a complete context management response.
        
        Args:
            analysis: Context analysis results
            optimization_result: Optional optimization results
            validation_errors: List of validation errors
            processing_time_ms: Processing time in milliseconds
            success: Whether the operation was successful
            message: Human-readable status message
            
        Returns:
            Formatted ContextManageResponse
        """
        try:
            # Format analysis response
            analysis_response = self.format_analysis_response(analysis)
            
            # Format optimization response if available
            optimization_response = None
            if optimization_result:
                optimization_response = self.format_optimization_response(
                    optimization_result, processing_time_ms
                )
            
            # Format validation response
            validation_response = ContextValidationResponse(
                is_valid=not validation_errors,
                errors=validation_errors or [],
                warnings=[]
            )
            
            # Format statistics
            statistics = self.format_statistics(analysis, optimization_result)
            
            # Create metadata
            metadata = {
                "processing_time_ms": processing_time_ms,
                "optimization_applied": optimization_result is not None,
                "version": self.version
            }
            
            return ContextManageResponse(
                success=success,
                message=message,
                analysis=analysis_response,
                optimization=optimization_response,
                validation=validation_response,
                statistics=statistics,
                metadata=metadata,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error formatting context manage response: {str(e)}")
            return self.format_error_response(
                error=f"Response formatting error: {str(e)}",
                code="FORMATTING_ERROR"
            )
    
    def format_analysis_response(self, analysis: ContextAnalysis) -> ContextAnalysisResponse:
        """
        Format context analysis results.
        
        Args:
            analysis: Context analysis results
            
        Returns:
            Formatted ContextAnalysisResponse
        """
        return ContextAnalysisResponse(
            total_tokens=analysis.total_tokens,
            total_items=len(analysis.tokens_by_type),
            tokens_by_type={ct.value: count for ct, count in analysis.tokens_by_type.items()},
            tokens_by_layer={lt.value: count for lt, count in analysis.tokens_by_layer.items()},
            optimization_needed=analysis.optimization_needed,
            compression_candidates=analysis.compression_candidates,
            recommendations=analysis.recommendations,
            utilization_ratio=analysis.total_tokens / 8000  # Default max tokens
        )
    
    def format_optimization_response(
        self, 
        optimization_result: ContextOptimizationResult,
        processing_time_ms: float
    ) -> ContextOptimizationResponse:
        """
        Format context optimization results.
        
        Args:
            optimization_result: Optimization results
            processing_time_ms: Processing time in milliseconds
            
        Returns:
            Formatted ContextOptimizationResponse
        """
        return ContextOptimizationResponse(
            optimized_content={ct.value: content for ct, content in optimization_result.optimized_content.items()},
            original_tokens=optimization_result.original_tokens,
            optimized_tokens=optimization_result.optimized_tokens,
            compression_ratio=optimization_result.compression_ratio,
            distillation_applied=optimization_result.distillation_applied,
            layers_compressed=[lt.value for lt in optimization_result.layers_compressed],
            token_reduction=optimization_result.original_tokens - optimization_result.optimized_tokens,
            processing_time_ms=processing_time_ms
        )
    
    def format_statistics(
        self, 
        analysis: ContextAnalysis,
        optimization_result: Optional[ContextOptimizationResult] = None
    ) -> ContextStatistics:
        """
        Format comprehensive context statistics.
        
        Args:
            analysis: Context analysis results
            optimization_result: Optional optimization results
            
        Returns:
            Formatted ContextStatistics
        """
        return ContextStatistics(
            total_items=len(analysis.tokens_by_type),
            total_tokens=optimization_result.optimized_tokens if optimization_result else analysis.total_tokens,
            tokens_by_type={ct.value: count for ct, count in analysis.tokens_by_type.items()},
            tokens_by_layer={lt.value: count for lt, count in analysis.tokens_by_layer.items()},
            optimization_needed=analysis.optimization_needed,
            compression_candidates=analysis.compression_candidates,
            recommendations=analysis.recommendations,
            utilization_ratio=analysis.total_tokens / 8000,  # Default max tokens
            distillation_threshold=6000,  # Default threshold
            max_context_tokens=8000  # Default max tokens
        )
    
    def format_error_response(
        self,
        error: str,
        details: List[ContextErrorDetail] = None,
        code: str = "CONTEXT_ERROR",
        request_id: Optional[str] = None
    ) -> ContextErrorResponse:
        """
        Format an error response.
        
        Args:
            error: Main error message
            details: Detailed error information
            code: Error code
            request_id: Optional request identifier
            
        Returns:
            Formatted ContextErrorResponse
        """
        return ContextErrorResponse(
            success=False,
            error=error,
            details=details or [],
            timestamp=datetime.utcnow(),
            request_id=request_id
        )
    
    def format_health_check_response(
        self,
        context_manager: ContextManager
    ) -> ContextHealthCheckResponse:
        """
        Format a health check response.
        
        Args:
            context_manager: ContextManager instance to check
            
        Returns:
            Formatted ContextHealthCheckResponse
        """
        try:
            # Check service status
            services = {
                "token_counter": "healthy",
                "token_allocator": "healthy", 
                "context_distiller": "healthy",
                "layer_hierarchy": "healthy"
            }
            
            # Test basic functionality
            try:
                # Simple test to verify services are working
                test_items = []
                analysis = context_manager.analyze_context(test_items)
                services["context_analysis"] = "healthy"
            except Exception as e:
                services["context_analysis"] = f"error: {str(e)}"
            
            configuration = {
                "max_context_tokens": context_manager.max_context_tokens,
                "distillation_threshold": context_manager.distillation_threshold,
                "enable_compression": context_manager.enable_compression,
                "version": self.version
            }
            
            overall_status = "healthy" if all(
                status == "healthy" for status in services.values()
            ) else "degraded"
            
            return ContextHealthCheckResponse(
                status=overall_status,
                version=self.version,
                services=services,
                configuration=configuration,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error in health check: {str(e)}")
            return ContextHealthCheckResponse(
                status="error",
                version=self.version,
                services={"error": str(e)},
                configuration={},
                timestamp=datetime.utcnow()
            )
    
    def format_optimized_context_data(
        self,
        optimization_result: ContextOptimizationResult
    ) -> OptimizedContextData:
        """
        Format optimized context data for integration with generation endpoints.
        
        Args:
            optimization_result: Context optimization results
            
        Returns:
            Formatted OptimizedContextData
        """
        try:
            # Extract content by type
            system_context = optimization_result.optimized_content.get("system", "")
            story_context = optimization_result.optimized_content.get("story", "")
            character_context = optimization_result.optimized_content.get("character", "")
            feedback_context = optimization_result.optimized_content.get("feedback", "")
            
            # Combine world and memory into story context if needed
            world_context = optimization_result.optimized_content.get("world", "")
            memory_context = optimization_result.optimized_content.get("memory", "")
            
            if world_context:
                story_context = f"{story_context}\n\n{world_context}".strip()
            
            if memory_context:
                feedback_context = f"{feedback_context}\n\n{memory_context}".strip()
            
            metadata = {
                "compression_ratio": optimization_result.compression_ratio,
                "distillation_applied": optimization_result.distillation_applied,
                "layers_compressed": [lt.value for lt in optimization_result.layers_compressed],
                "original_tokens": optimization_result.original_tokens,
                "token_reduction": optimization_result.original_tokens - optimization_result.optimized_tokens
            }
            
            return OptimizedContextData(
                system_context=system_context,
                story_context=story_context,
                character_context=character_context,
                feedback_context=feedback_context,
                total_tokens=optimization_result.optimized_tokens,
                compression_applied=optimization_result.distillation_applied,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error formatting optimized context data: {str(e)}")
            # Return minimal data structure on error
            return OptimizedContextData(
                system_context="",
                story_context="",
                character_context="",
                feedback_context="",
                total_tokens=0,
                compression_applied=False,
                metadata={"error": str(e)}
            )


def create_error_detail(
    code: str,
    message: str,
    field: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> ContextErrorDetail:
    """
    Create a detailed error information object.
    
    Args:
        code: Error code
        message: Error message
        field: Optional field that caused the error
        context: Optional additional context
        
    Returns:
        ContextErrorDetail object
    """
    return ContextErrorDetail(
        code=code,
        message=message,
        field=field,
        context=context
    )


def format_validation_errors(errors: List[str]) -> List[ContextErrorDetail]:
    """
    Format validation errors into detailed error objects.
    
    Args:
        errors: List of validation error messages
        
    Returns:
        List of ContextErrorDetail objects
    """
    details = []
    for error in errors:
        # Try to extract field information from error message
        field = None
        if ":" in error:
            parts = error.split(":", 1)
            if len(parts) == 2:
                potential_field = parts[0].strip()
                if not potential_field.startswith("Item"):
                    field = potential_field
        
        details.append(ContextErrorDetail(
            code="VALIDATION_ERROR",
            message=error,
            field=field
        ))
    
    return details


def measure_processing_time(start_time: float) -> float:
    """
    Calculate processing time in milliseconds.
    
    Args:
        start_time: Start time from time.time()
        
    Returns:
        Processing time in milliseconds
    """
    return (time.time() - start_time) * 1000


def format_token_summary(
    original_tokens: int,
    optimized_tokens: int,
    target_tokens: Optional[int] = None
) -> str:
    """
    Format a human-readable token summary.
    
    Args:
        original_tokens: Original token count
        optimized_tokens: Optimized token count
        target_tokens: Optional target token count
        
    Returns:
        Formatted summary string
    """
    reduction = original_tokens - optimized_tokens
    reduction_pct = (reduction / original_tokens * 100) if original_tokens > 0 else 0
    
    summary = f"Reduced from {original_tokens:,} to {optimized_tokens:,} tokens ({reduction:,} tokens, {reduction_pct:.1f}% reduction)"
    
    if target_tokens:
        if optimized_tokens <= target_tokens:
            summary += f" - Target of {target_tokens:,} tokens achieved"
        else:
            overage = optimized_tokens - target_tokens
            summary += f" - Target of {target_tokens:,} tokens exceeded by {overage:,} tokens"
    
    return summary


def format_recommendations_list(recommendations: List[str]) -> str:
    """
    Format recommendations as a readable list.
    
    Args:
        recommendations: List of recommendation strings
        
    Returns:
        Formatted recommendations string
    """
    if not recommendations:
        return "No specific recommendations."
    
    if len(recommendations) == 1:
        return recommendations[0]
    
    formatted = "Recommendations:\n"
    for i, rec in enumerate(recommendations, 1):
        formatted += f"{i}. {rec}\n"
    
    return formatted.strip()
