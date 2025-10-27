"""
Pydantic models for phase validation API.
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel
from .generation_models import ComposePhase


class PhaseTransitionRequest(BaseModel):
    """Request model for phase transition validation."""
    from_phase: ComposePhase
    to_phase: ComposePhase
    phase_output: str
    story_context: Dict[str, Any]


class ValidationResult(BaseModel):
    """Individual validation result."""
    criterion: str
    passed: bool
    message: str
    score: Optional[float] = None


class PhaseTransitionResponse(BaseModel):
    """Response model for phase transition validation."""
    valid: bool
    overall_score: float
    validation_results: list[ValidationResult]
    recommendations: list[str]
    metadata: Dict[str, Any]
