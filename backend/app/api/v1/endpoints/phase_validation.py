"""
Phase validation endpoint for three-phase chapter compose system.
"""
from fastapi import APIRouter, HTTPException
from app.models.phase_models import PhaseTransitionRequest, PhaseTransitionResponse, ValidationResult
from app.services.llm_inference import get_llm
from datetime import datetime, UTC
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


def _validate_plot_outline_to_chapter_detail(phase_output: str, story_context: dict) -> list[ValidationResult]:
    """Validate transition from plot outline to chapter detail phase."""
    results = []
    
    # Check if plot outline has sufficient detail
    word_count = len(phase_output.split())
    results.append(ValidationResult(
        criterion="Plot outline length",
        passed=word_count >= 50,
        message=f"Plot outline has {word_count} words (minimum 50 required)",
        score=min(1.0, word_count / 50)
    ))
    
    # Check for key story elements
    has_conflict = any(word in phase_output.lower() for word in ['conflict', 'problem', 'challenge', 'obstacle'])
    results.append(ValidationResult(
        criterion="Conflict presence",
        passed=has_conflict,
        message="Plot outline includes conflict or challenge" if has_conflict else "Plot outline should include conflict or challenge",
        score=1.0 if has_conflict else 0.3
    ))
    
    # Check for character involvement
    has_characters = any(word in phase_output.lower() for word in ['character', 'protagonist', 'he', 'she', 'they'])
    results.append(ValidationResult(
        criterion="Character involvement",
        passed=has_characters,
        message="Plot outline includes character references" if has_characters else "Plot outline should reference characters",
        score=1.0 if has_characters else 0.2
    ))
    
    return results


def _validate_chapter_detail_to_final_edit(phase_output: str, story_context: dict) -> list[ValidationResult]:
    """Validate transition from chapter detail to final edit phase."""
    results = []
    
    # Check chapter length
    word_count = len(phase_output.split())
    results.append(ValidationResult(
        criterion="Chapter length",
        passed=word_count >= 500,
        message=f"Chapter has {word_count} words (minimum 500 for editing)",
        score=min(1.0, word_count / 500)
    ))
    
    # Check for dialogue
    has_dialogue = '"' in phase_output or "'" in phase_output
    results.append(ValidationResult(
        criterion="Dialogue presence",
        passed=has_dialogue,
        message="Chapter includes dialogue" if has_dialogue else "Consider adding dialogue to enhance the chapter",
        score=1.0 if has_dialogue else 0.7
    ))
    
    # Check for narrative structure
    paragraph_count = len([p for p in phase_output.split('\n\n') if p.strip()])
    results.append(ValidationResult(
        criterion="Narrative structure",
        passed=paragraph_count >= 3,
        message=f"Chapter has {paragraph_count} paragraphs (good structure)" if paragraph_count >= 3 else "Chapter could benefit from more paragraph breaks",
        score=min(1.0, paragraph_count / 3)
    ))
    
    return results


def _validate_plot_outline_to_final_edit(phase_output: str, story_context: dict) -> list[ValidationResult]:
    """Validate direct transition from plot outline to final edit (skip chapter detail)."""
    results = []
    
    # This is generally not recommended, so add a warning
    results.append(ValidationResult(
        criterion="Phase sequence",
        passed=False,
        message="Skipping chapter detail phase is not recommended for best results",
        score=0.5
    ))
    
    # Still validate basic requirements
    word_count = len(phase_output.split())
    results.append(ValidationResult(
        criterion="Content length",
        passed=word_count >= 200,
        message=f"Content has {word_count} words (minimum 200 for final editing)",
        score=min(1.0, word_count / 200)
    ))
    
    return results


@router.post("/validate/phase-transition", response_model=PhaseTransitionResponse)
async def validate_phase_transition(request: PhaseTransitionRequest):
    """
    Validate transition between phases in the three-phase compose system.
    """
    try:
        # Determine validation logic based on phase transition
        if request.from_phase == "plot_outline" and request.to_phase == "chapter_detail":
            validation_results = _validate_plot_outline_to_chapter_detail(request.phase_output, request.story_context)
        elif request.from_phase == "chapter_detail" and request.to_phase == "final_edit":
            validation_results = _validate_chapter_detail_to_final_edit(request.phase_output, request.story_context)
        elif request.from_phase == "plot_outline" and request.to_phase == "final_edit":
            validation_results = _validate_plot_outline_to_final_edit(request.phase_output, request.story_context)
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid phase transition: {request.from_phase} -> {request.to_phase}"
            )
        
        # Calculate overall score
        if validation_results:
            overall_score = sum(result.score or 0 for result in validation_results) / len(validation_results)
        else:
            overall_score = 0.0
        
        # Determine if transition is valid (threshold: 0.7)
        valid = overall_score >= 0.7
        
        # Generate recommendations
        recommendations = []
        for result in validation_results:
            if not result.passed:
                recommendations.append(result.message)
        
        if not recommendations:
            recommendations.append("Phase output meets requirements for transition.")
        
        return PhaseTransitionResponse(
            valid=valid,
            overall_score=overall_score,
            validation_results=validation_results,
            recommendations=recommendations,
            metadata={
                "validatedAt": datetime.now(UTC).isoformat(),
                "fromPhase": request.from_phase,
                "toPhase": request.to_phase,
                "outputWordCount": len(request.phase_output.split()),
                "threshold": 0.7
            }
        )
        
    except Exception as e:
        logger.error(f"Error in validate_phase_transition: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error validating phase transition: {str(e)}")
